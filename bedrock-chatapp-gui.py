import boto3, botocore, json, os, logging
import tkinter as tk
from tkinter import ttk, Label, Scrollbar, Text, Button, font, filedialog, simpledialog, messagebox
from PIL import Image, ImageTk
import threading
import queue
import configparser
import base64
import mimetypes
import os
from io import BytesIO
import fitz  # PyMuPDF 转换pdf 
import socket
import socks
os.environ['OS_ACTIVITY_DT_MODE'] = 'disable' 
default_socks = socket.socket

# default values
MAX_RETRIES = 3 
MAX_SIZE_IN_MB = 5
max_size = MAX_SIZE_IN_MB * 1024 * 1024  # 5MB 转换为字节
custom_font_size = 12
accept = 'application/json'
contentType = 'application/json'
default_intruction = {"default": "你是一个用中文回答问题的AI机器人，你会一步步地思考"}
sys_prompt_path = os.path.join(os.getcwd(), "bedrock_chatapp_prompt.json")
global rewrite_text
try:
    with open(sys_prompt_path, 'r', encoding="utf-8") as f:
        sys_prompt_dict = json.load(f)
except FileNotFoundError:
    sys_prompt_dict = default_intruction
    
def get_regions():
    return ('us-west-2', 'us-east-1', 'ap-southeast-1', 'ap-northeast-1', 'eu-central-1', 'ap-southeast-2', 'eu-west-3', 'ap-south-1')

def get_modelIds():
    return ('us.anthropic.claude-3-7-sonnet-20250219-v1:0', 'us.anthropic.claude-sonnet-4-20250514-v1:0', 'us.anthropic.claude-opus-4-20250514-v1:0', 'us.deepseek.r1-v1:0', 'us.amazon.nova-premier-v1:0', 'anthropic.claude-3-5-sonnet-20241022-v2:0', 'anthropic.claude-3-5-haiku-20241022-v1:0', 'us.amazon.nova-pro-v1:0','us.amazon.nova-lite-v1:0', 'us.amazon.nova-micro-v1:0')

def get_proxy():
    return ('NoProxy', 'Local')

default_para = {  # 可以在运行之后的界面上修改
    "us.anthropic.claude-sonnet-4-20250514-v1:0": {
        "No-Think": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 32000,
            "temperature": 0.5, 
            "top_k": 250,       
            "top_p": 1,         
        },
        "Think": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 32000,
            "thinking": {
                "type": "enabled",
                "budget_tokens": 16000
            },
        },
    },
    "us.anthropic.claude-opus-4-20250514-v1:0": {
        "No-Think": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 32000,
            "temperature": 0.5, 
            "top_k": 250,       
            "top_p": 1,         
        },
        "Think": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 32000,
            "thinking": {
                "type": "enabled",
                "budget_tokens": 16000
            },
        },
    },
    "us.deepseek.r1-v1:0": {
        "Default": {
            "temperature": 0.5,
            "top_p": 0.9,
            "max_tokens": 32768,
        },
    },
    "anthropic.claude-3-5-sonnet-20241022-v2:0": {
        "Default": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "temperature": 0.5, # Use a lower value to decrease randomness in the response. Claude 0-1, default 0.5
            "top_k": 250,       # Use a lower value to ignore less probable options.  Claude 0-500, default 250
            "top_p": 1,         # Specify the number of token choices the model uses to generate the next token. Claude 0-1, default 1
            "stop_sequences": ["end_turn"],
        },
    },
    "anthropic.claude-3-5-haiku-20241022-v1:0": {
        "Default": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 8192,
            "temperature": 0.5, 
            "top_k": 250,       
            "top_p": 1,         
            "stop_sequences": ["end_turn"],
        },
    },
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0": {
        "No-Think": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 32000,
            "temperature": 0.5, 
            "top_k": 250,       
            "top_p": 1,         
        },
        "Think": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 64000,
            "thinking": {
                "type": "enabled",
                "budget_tokens": 32000
            },
        },
    },
    "us.amazon.nova-premier-v1:0": {
        "Default": {
            "max_new_tokens": 32000,
            "temperature": 0.7, 
            "top_k": 20,       
            "top_p": 0.9,
        },
    },
    "us.amazon.nova-pro-v1:0": {
        "Default": {
            "max_new_tokens": 10000,
            "temperature": 0.7, 
            "top_k": 20,       
            "top_p": 0.9,
        },
    },
    "us.amazon.nova-lite-v1:0": {
        "Default": {
            "max_new_tokens": 10000,
            "temperature": 0.7, 
            "top_k": 20,       
            "top_p": 0.9,
        },
    },
    "us.amazon.nova-micro-v1:0": {
        "Default": {
            "max_new_tokens": 10000,
            "temperature": 0.7, 
            "top_k": 20,       
            "top_p": 0.9,
        },
    }
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logpath='./bedrock_chatapp_history.log'
file_handler = logging.FileHandler(logpath, encoding='utf-8')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y%m%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_profiles():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials'))
    return config.sections()

def set_profile():
    pro_conf = configparser.RawConfigParser()
    pro_path = os.path.join(os.path.expanduser("~"), ".aws")
    cre_path = os.path.join(pro_path, "credentials")
    if not os.path.exists(cre_path):
        print(f"There is no aws_access_key in {cre_path}, please input IAM User Credentials for your AWS account: ")
        if not os.path.exists(pro_path):
            os.mkdir(pro_path)
        aws_access_key_id = input('aws_access_key_id: ')
        aws_secret_access_key = input('aws_secret_access_key: ')
        region = input('region(e.g. us-east-1): ')
        pro_conf.add_section('default')
        pro_conf['default']['aws_access_key_id'] = aws_access_key_id
        pro_conf['default']['aws_secret_access_key'] = aws_secret_access_key
        pro_conf['default']['region'] = region
        with open(cre_path, 'w') as f:
            print(f"Saving credentials to {cre_path}")
            pro_conf.write(f)

class ChatApp:
    def __init__(self, root):
        self.root = root
        # self.root.configure(bg='white')
        title_text = f"AWS Bedrock ChatApp by James Huang, chat log in:{os.path.abspath(logpath)}"
        self.root.title(title_text)
        self.root.geometry('1200x800')
        # Set the column and row weights
        self.root.grid_columnconfigure(0, weight=4)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        custom_font = font.Font(size=custom_font_size)

        # Create a frame for the profile and region selectors
        selector_frame = tk.Frame(root)
        selector_frame.grid(row=0, column=0, columnspan=2, sticky='nsew')

        Label(selector_frame, text="AWS Profile").pack(side=tk.LEFT)
        profiles = get_profiles()
        self.profile_var = tk.StringVar()
        self.profile_var.set(profiles[0] if profiles else "No Profile Found")
        self.profile_menu = ttk.Combobox(selector_frame, width=5, textvariable=self.profile_var, values=profiles, state="readonly")
        self.profile_menu.pack(side=tk.LEFT)
        self.profile_menu.bind("<<ComboboxSelected>>", self.change_profile_region)

        Label(selector_frame, text="Region").pack(side=tk.LEFT)
        regions = get_regions()
        self.region_var = tk.StringVar()
        self.region_var.set(regions[0] if regions else "No Region Found")
        self.region_menu = ttk.Combobox(selector_frame, width=10, textvariable=self.region_var, values=regions, state="readonly")
        self.region_menu.pack(side=tk.LEFT)
        self.region_menu.bind("<<ComboboxSelected>>", self.change_profile_region)

        Label(selector_frame, text="Proxy").pack(side=tk.LEFT)
        proxy = get_proxy()
        self.proxy_var = tk.StringVar()
        self.proxy_var.set(proxy[0] if proxy else "No Proxy Found")
        self.proxy_var_menu = ttk.Combobox(selector_frame, width=5, textvariable=self.proxy_var, values=proxy, state="readonly")
        self.proxy_var_menu.pack(side=tk.LEFT)
        self.proxy_var_menu.bind("<<ComboboxSelected>>", self.change_profile_region)

        Label(selector_frame, text="Model").pack(side=tk.LEFT)
        modelIds = get_modelIds()
        self.modelId_var = tk.StringVar()
        self.modelId_var.set(modelIds[0] if modelIds else "No ModelId Found")
        self.modelId_menu = ttk.Combobox(selector_frame, width=30, textvariable=self.modelId_var, values=modelIds, state="readonly")
        self.modelId_menu.pack(side=tk.LEFT)
        self.modelId_menu.bind("<<ComboboxSelected>>", self.change_modelId)
        
        # 添加参数预设选择器
        Label(selector_frame, text="ModelPara").pack(side=tk.LEFT)
        self.preset_var = tk.StringVar()
        self.preset_var.set("Default")
        self.preset_menu = ttk.Combobox(selector_frame, width=10, textvariable=self.preset_var, values=["Default"], state="readonly")
        self.preset_menu.pack(side=tk.LEFT)
        self.preset_menu.bind("<<ComboboxSelected>>", self.change_preset)

        Label(selector_frame, text="Font").pack(side=tk.LEFT)
        fontSize = ('8', '10', '12', '14', '16', '18', '20', '22', '24', '26', '28')
        self.fontSize_var = tk.StringVar()
        self.fontSize_var.set(str(custom_font.cget("size")) if fontSize else "No Font Found")
        self.fontSize_menu = ttk.Combobox(selector_frame, width=3, textvariable=self.fontSize_var, values=fontSize, state="readonly")
        self.fontSize_menu.pack(side=tk.LEFT)
        self.fontSize_menu.bind("<<ComboboxSelected>>", self.change_fontSize)
        
        # para frame
        bedrock_para_frame = tk.Frame(root)
        bedrock_para_frame.grid(row=1, column=1, rowspan=2, sticky='nsew')
        bedrock_para_frame.grid_columnconfigure(0, weight=1)
        bedrock_para_frame.grid_rowconfigure(1, weight=1)
        bedrock_para_frame.grid_rowconfigure(4, weight=1)

        Label(bedrock_para_frame, text="Model Para Detail").grid(row=0, column=0, sticky='w')
        self.bedrock_para = tk.StringVar()
        self.bedrock_para.set(json.dumps(default_para, indent=1))
        self.bedrock_para_text = Text(bedrock_para_frame, font=custom_font, width=15, height=5)
        self.bedrock_para_text.insert(tk.END, self.bedrock_para.get())
        self.bedrock_para_text.grid(row=1, column=0, sticky='nsew')

        syspromote_frame = tk.Frame(bedrock_para_frame)
        syspromote_frame.grid(row=2, column=0, sticky='nsew', pady=5)
        syspromote_frame_label = tk.Label(syspromote_frame, text="System Prompt: ")
        syspromote_frame_label.grid(row=0, column=0, sticky='w')
        self.sys_prompt_list = list(sys_prompt_dict.keys())
        self.sys_prompt_var = tk.StringVar()
        self.sys_prompt_var.set(self.sys_prompt_list[0])
        self.sys_prompt_menu = ttk.Combobox(syspromote_frame, textvariable=self.sys_prompt_var, values=self.sys_prompt_list, width=10, state="readonly")
        self.sys_prompt_menu.grid(row=0, column=1, sticky='ew')
        self.sys_prompt_menu.bind("<<ComboboxSelected>>", self.change_sysprompt)

        # Frame for prompt buttons 
        prompt_button_frame = tk.Frame(bedrock_para_frame)
        prompt_button_frame.grid(row=3, column=0, sticky='ew')
        new_button = tk.Button(prompt_button_frame, text="New", command=self.new_sys_prompt)
        new_button.grid(row=0, column=0, sticky='e')
        save_button = tk.Button(prompt_button_frame, text="Save", command=self.save_sys_prompt)
        save_button.grid(row=0, column=1, sticky='e')
        del_button = tk.Button(prompt_button_frame, text="Delete", command=self.del_sys_prompt)
        del_button.grid(row=0, column=2, sticky='e')
        self.instruction_text = Text(bedrock_para_frame, font=custom_font, width=15)
        self.instruction_text.grid(row=4, column=0, sticky='nsew')

        # Create a PanedWindow for the text history and input
        self.paned_window = ttk.PanedWindow(root, orient=tk.VERTICAL)
        self.paned_window.grid(row=1, column=0, sticky="nsew")

        history_frame = tk.Frame(self.paned_window)
        self.paned_window.add(history_frame)
        history_frame.grid_rowconfigure(0, weight=1)
        history_frame.grid_columnconfigure(0, weight=1)
        self.scrollbar = Scrollbar(history_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history = Text(history_frame, font=custom_font, yscrollcommand=self.scrollbar.set)
        self.history.pack(fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.history.yview)
        self.history.images = []

        entry_frame = tk.Frame(self.paned_window)
        self.paned_window.add(entry_frame)
        entry_frame.grid_rowconfigure(0, weight=1)
        entry_frame.grid_columnconfigure(0, weight=1) 
        self.scrollbar2 = Scrollbar(entry_frame)
        self.scrollbar2.pack(side=tk.RIGHT, fill=tk.Y)

        self.entry = Text(entry_frame, font=custom_font, yscrollcommand=self.scrollbar2.set)
        self.entry.pack(fill=tk.BOTH, expand=True)
        self.scrollbar2.config(command=self.entry.yview)
        self.entry.focus_set()
        self.entry.bind("<Return>", self.send_message)
        self.entry.bind("<Control-s>", self.send_message)
        self.entry.bind("<Shift-Return>", self.just_enter)
        self.entry.bind("<Command-Return>", self.just_enter)
        self.entry.bind("<Control-l>", self.clear_history)

        inputbar_frame = tk.Frame(root)
        inputbar_frame.grid(row=2, column=0, sticky="ew", padx=2, pady=2)
        inputbar_frame.grid_columnconfigure(6, weight=1)
        self.clear_button = Button(inputbar_frame, text="ClearContext", command=self.clear_history, width=12, height=1)
        self.clear_button.grid(row=0, column=0, sticky='ew')
        self.clean_button = Button(inputbar_frame, text="CleanScreen", command=self.clean_screen, width=12, height=1)
        self.clean_button.grid(row=0, column=1, sticky='ew')
        self.browser_button = Button(inputbar_frame, text="FILE", command=self.browse_file, width=12, height=1)
        self.browser_button.grid(row=0, column=2, sticky='ew')
        rewrite_buton = tk.Button(inputbar_frame, text="Rewrite", width=12, height=1, command=self.rewrite)
        rewrite_buton.grid(row=0, column=3, padx=5)
        self.remember_history = tk.BooleanVar()
        self.remember_history.set(True)
        self.remember_history_checkbox = tk.Checkbutton(inputbar_frame, text="Remember Context", variable=self.remember_history, command=self.check_remember_history)
        self.remember_history_checkbox.grid(row=0, column=4, sticky="w")
        self.history_num = Label(inputbar_frame, text="| History: 0 |")
        self.history_num.grid(row=0, column=5, sticky='ew')
        self.send_button = Button(inputbar_frame, text="SEND", command=self.send_message, underline=0, width=12, height=1)
        self.send_button.grid(row=0, column=6, sticky='e')

        self.change_profile_region()
        self.change_modelId()
        self.change_sysprompt()
        self.chat_history = []
        self.file_content = []
        self.queue = queue.Queue()
        self.root.after(1000, self.check_queue)
            
        # Add window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        self.cleanup()
        self.root.destroy()

    def change_profile_region(self, event=None):
        self.profile = self.profile_var.get()
        self.region = self.region_var.get()
        self.proxy = self.proxy_var.get()

    def change_modelId(self, event=None):
        self.modelId = self.modelId_var.get()
        # 更新参数预设下拉菜单
        presets = list(default_para[self.modelId].keys())
        self.preset_var.set(presets[0])  # 默认选择第一个预设
        self.preset_menu['values'] = presets
        # 更新参数显示
        self.change_preset()
        
    def change_preset(self, event=None):
        preset = self.preset_var.get()
        self.bedrock_para_text.delete("1.0", tk.END)
        self.bedrock_para_text.insert(tk.END, json.dumps(default_para[self.modelId][preset], indent=1))

    def change_fontSize(self, event=None):
        self.fontSize = self.fontSize_var.get()
        self.custom_font = font.Font(size=int(self.fontSize))
        self.history.config(font=self.custom_font)
        self.entry.config(font=self.custom_font)
        self.bedrock_para_text.config(font=self.custom_font)
        self.instruction_text.config(font=self.custom_font)

    def save_history(self, history_record):     
        self.chat_history.append(history_record)
        #self.history_num.config(text=f"| History: {len(self.chat_history)} |")
        return

    def just_enter(self, event=None):
        return

    def rewrite(self, event=None):
        self.entry.delete("1.0", tk.END)
        self.entry.insert(tk.END, rewrite_text)

    # 清理历史消息，后面的对话将不会考虑Clear之前的历史上下文
    def clear_history(self, event=None):
        answers = "\n------ Context Cleared ------\n\n"
        self.queue.put(answers)
        logger.info(answers)
        self.file_content = []
        self.chat_history = []
        self.history_num.config(text=f"History: {len(self.chat_history)}")
    
    def clean_screen(self, event=None):
        self.history.delete("1.0", tk.END)
        self.clear_history()

    # 发送消息按钮
    def send_message(self, event=None):
        global rewrite_text
        try:
            # Pause input and send button
            # self.send_button.config(state=tk.DISABLED)
            self.entry.unbind("<Return>")
            self.entry.unbind("<Control-s>")

            # Construct context
            question = self.entry.get("1.0", tk.END).strip()
            rewrite_text = question
            if question == "":
                question = "?"
            self.history.insert(tk.END, "User: " + question + '\n\n')
            self.history.see(tk.END)

            # 多模态上传文件
            if self.file_content:
                if 'amazon.nova-' in self.modelId:
                    self.file_content.append({
                            "text": question
                        })
                elif 'anthropic.claude-' in self.modelId:
                    self.file_content.append({
                            "type": "text",
                            "text": question
                        })
                user_message = {"role": "user", "content": self.file_content}
                self.file_content = []  # 清空上传文件的内容
            # 纯文本交互
            else:
                if 'amazon.nova-' in self.modelId:
                    user_message = {"role": "user", "content": [{"text": question}]}
                elif 'anthropic.claude-' in self.modelId:
                    user_message = {"role": "user", "content": question}
                elif 'deepseek' in self.modelId:
                    user_message = {"role": "user", "content": question}

            self.save_history(user_message)
            logger.info(json.dumps(user_message, ensure_ascii=False))
            system_prompt = self.instruction_text.get("1.0", tk.END).strip()
            prompt = self.chat_history
            self.history.insert(tk.END, f"Bot({self.modelId}): ")
            self.history.see(tk.END)

            # Construct bedrock_para
            if 'amazon.nova-' in self.modelId:
                bedrock_para = {
                    "inferenceConfig": json.loads(self.bedrock_para_text.get("1.0", tk.END).strip()),
                    "schemaVersion": "messages-v1",
                    "system": [{"text": system_prompt}],
                    "messages": prompt
                }
            elif 'anthropic.claude-' in self.modelId:
                bedrock_para = json.loads(self.bedrock_para_text.get("1.0", tk.END).strip())
                bedrock_para['system'] = system_prompt
                bedrock_para['messages'] = prompt
            elif 'deepseek' in self.modelId:
                bedrock_para = json.loads(self.bedrock_para_text.get("1.0", tk.END).strip())
                #formatted_prompt = f"""<｜begin▁of▁sentence｜><System>{system_prompt}<｜User｜>{prompt}\n"""
                formatted_prompt = f"""<｜begin▁of▁sentence｜><｜User｜>{prompt}<｜Assistant｜><think>\n"""
                bedrock_para['prompt'] = formatted_prompt

            invoke_body = json.dumps(bedrock_para)
            # 异步调用Bedrock API
            threading.Thread(target=self.generate_reply, args=(invoke_body,)).start()
            self.entry.delete("1.0", tk.END)
        except Exception as e:
            self.history.insert(tk.END, "Error instruction: " + str(e) + '\n')
        return "break"

    # 异步调用Bedrock API
    def generate_reply(self, invoke_body):
        answers = ""
        try:
            # 每次调用都创建一个新的连接，避免idle导致连接断开，从而输入无响应等问题
            session = boto3.Session(profile_name=self.profile) 
            if self.proxy == "NoProxy":
                socket.socket = default_socks
                clientConfig = botocore.config.Config(retries={'max_attempts': MAX_RETRIES},
                                                      connect_timeout=15,
                                                      read_timeout=15)

            elif self.proxy == "Local":
                # Set up the SOCKS proxy at the socket level
                socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 1088)
                socket.socket = socks.socksocket
                clientConfig = botocore.config.Config(retries={'max_attempts': MAX_RETRIES},
                                                      connect_timeout=15,
                                                      read_timeout=15)
            self.client = session.client("bedrock-runtime", region_name=self.region, config=clientConfig)

            # Invoke streaming model 
            response = self.client.invoke_model_with_response_stream(body=invoke_body, modelId=self.modelId, accept=accept, contentType=contentType)
            for event in response.get('body'):
                answer = ""
                chunk_str = json.loads(event['chunk']['bytes'].decode('utf-8'))
                if 'amazon.nova-' in self.modelId:
                    content_block_delta = chunk_str.get("contentBlockDelta")
                    invocationMetrics = chunk_str.get("amazon-bedrock-invocationMetrics")
                    if invocationMetrics:
                        hints = "\n"+json.dumps(invocationMetrics)
                    else:
                        hints = ""
                    if content_block_delta:
                        answer = content_block_delta.get("delta").get("text")
                elif 'anthropic.claude-' in self.modelId:
                    if chunk_str['type'] == "message_start":
                        input_tokens = json.dumps(chunk_str['message']['usage']['input_tokens'])
                        hints = f"Input tokens: {input_tokens}\n******Answer******\n"
                    elif chunk_str['type'] == "content_block_start" and chunk_str['content_block']['type'] == 'thinking':
                            answer = "\n***Thinking START***\n"
                    elif chunk_str['type'] == "content_block_delta":
                        if chunk_str['delta']['type'] == 'text_delta':
                            answer = chunk_str['delta']['text']
                        elif chunk_str['delta']['type'] == 'thinking_delta':
                            answer = chunk_str['delta']['thinking']
                        elif chunk_str['delta']['type'] == 'signature_delta':
                            answer = "\n***Thinking END***\n\n"
                    elif chunk_str['type'] == "message_delta":
                        hints=f"""\n******Answer END******\n\nStop reason: {chunk_str['delta']['stop_reason']}; Stop sequence: {chunk_str['delta']['stop_sequence']}; Output tokens: {chunk_str['usage']['output_tokens']}\n\n"""
                    elif chunk_str['type'] == "error":
                        hints=json.dumps(chunk_str)
                elif 'deepseek' in self.modelId:
                    choices = chunk_str['choices']
                    answer = choices[0]['text']
                    if 'amazon-bedrock-invocationMetrics' in chunk_str:
                        usage = chunk_str['amazon-bedrock-invocationMetrics']
                        hints = f"""\n******Answer END******\n\nInput tokens: {usage['inputTokenCount']}; Output tokens: {usage['outputTokenCount']}\n"""
                    else:
                        hints = ""
                    if choices[0]['stop_reason'] is not None:
                        hints += f"Stop reason: {choices[0]['stop_reason']}\n\n"
                    

                if hints:
                    self.queue.put(hints)
                    hints = ""
                else:
                    self.queue.put(answer)
                    answers += answer

        except Exception as e:
            self.queue.put(f"\n\nError: {str(e)}\n")
        
        if 'amazon.nova-' in self.modelId:
            history_record = {"role": "assistant", "content": [{"text": answers}]}
        elif 'anthropic.claude-' in self.modelId:
            history_record = {"role": "assistant", "content": answers}
        elif 'deepseek' in self.modelId:
            history_record = {"role": "assistant", "content": answers}

        self.save_history(history_record)
        logger.info(json.dumps(history_record, ensure_ascii=False))
        self.queue.put("\n---END---\n\n")
        # self.send_button.config(state=tk.NORMAL)
        self.entry.bind("<Return>", self.send_message)
        self.entry.bind("<Control-s>", self.send_message)
        if self.remember_history.get() == False:
            self.clear_history()
        return

    # 异步打印Bedrock返回消息
    def check_queue(self):
        try:
            while not self.queue.empty():
                answer = self.queue.get_nowait()  # Use get_nowait() instead of get()
                if self.history and self.history.winfo_exists():  # Check if widget still exists
                    self.history.insert(tk.END, answer)
                    self.history.see(tk.END)
            # Schedule next check only if root window exists
            if self.root and self.root.winfo_exists():
                self.root.after(1000, self.check_queue)
        except Exception as e:
            logger.error(f"Error in check_queue: {str(e)}")

    def cleanup(self):
        # Cancel any pending after callbacks
        if hasattr(self, 'root') and self.root:
            self.root.after_cancel(self.check_queue)
        
        # Clear queue
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except queue.Empty:
                break

    # process upload image and display
    def handle_image(self, image, file_name, mime_type):
        # Use default format png if no format detected
        save_format = (image.format or "png").lower()
        width, height = image.size

        if width > 1568 or height > 1568:
            max_dim = max(width, height)
            ratio = 1568 / max_dim
            width = int(width * ratio)
            height = int(height * ratio)
            image = image.resize((width, height))
        # 将缩小后的图像保存在内存中，试算一下图片大小
        buffer = BytesIO()
        image.save(buffer, format=save_format)
        image_bytes = buffer.getvalue()
        buffer.close()

        # 如果图片大小大于 5MB,则缩小图片，否则Bedrock不接受
        image_size = len(image_bytes)
        if image_size > max_size:
            ratio = (max_size / image_size) ** 0.5
            width = int(width * ratio)
            height = int(height * ratio)
            image = image.resize((width, height))
            buffer = BytesIO()
            image.save(buffer, format=save_format)
            image_bytes = buffer.getvalue()
            buffer.close()

        encoded_string = base64.b64encode(image_bytes)
        if 'amazon.nova-' in self.modelId:
            self.file_content.append({
                            "image": {
                                "format": save_format,
                                "source": {
                                    "bytes": encoded_string.decode('utf-8')
                                }
                            }
                            })

        elif 'anthropic.claude-' in self.modelId:
            self.file_content.append({
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime_type,
                                "data": encoded_string.decode('utf-8')
                            }})

        # 改变"显示"的分辨率大小为500以内
        if width > 512:
            image = image.resize((512, int(height * 512 / width)))
        photo = ImageTk.PhotoImage(image)
        self.history.image_create(tk.END, image=photo)
        self.history.images.append(photo)
        self.history.insert(tk.END, f"\nImage: {file_name}, Resolution: {width}x{height}\n\n")
    
    # Click Select File
    def browse_file(self):
        local_files = filedialog.askopenfilenames(title='Select Files')
        for local_file in local_files:
            file_name = os.path.basename(local_file)
            mime_type = mimetypes.guess_type(local_file)[0]
            
            # 图片类型直接处理
            if mime_type[0:5] == 'image': 
                image = Image.open(local_file)
                self.handle_image(image, file_name, mime_type)
                image.close()

            # PDF
            if mime_type == 'application/pdf':
                try:
                    with open(local_file, "rb") as pdf_document:
                        pdf_string = pdf_document.read()
                        if pdf_string:
                            pdf_string = base64.b64encode(pdf_string)
                            if 'amazon.nova-' in self.modelId:
                                self.file_content.append({
                                    "document": {
                                        "format": "pdf",
                                        "name": file_name,
                                        "source": {
                                            "bytes": pdf_string.decode('utf-8')
                                        }
                                    }
                                    })

                            elif 'anthropic.claude-' in self.modelId:
                                self.file_content.append({
                                    "type": "document",
                                    "source":{
                                        "type": "base64",
                                        "media_type": "application/pdf",
                                        "data": pdf_string.decode('utf-8'),
                                        },
                                    "title": file_name,
                                    "citations": {"enabled": True},
                                    # "cache_control": {"type": "ephemeral"}
                                }
                                )
                    # pdf_document = fitz.open(local_file)
                    # for page_num, page in enumerate(pdf_document):
                    #     output_pdf = fitz.open()
                    #     output_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
                    #     doc_bytes = output_pdf.tobytes()
                    #     if doc_bytes:
                    #         pdf_string = base64.b64encode(doc_bytes)
                    #         if 'amazon.nova-' in self.modelId:
                    #             self.file_content.append({
                    #                 "document": {
                    #                     "format": "pdf",
                    #                     "name": f"{file_name}_page_{page_num + 1}",
                    #                     "source": {
                    #                         "bytes": pdf_string.decode('utf-8')
                    #                     }
                    #                 }
                    #                 })

                    #         elif 'anthropic.claude-' in self.modelId:
                    #             # Now Claude support PDF 100 pages
                    #             if len(self.file_content) >= 100:
                    #                 messagebox.showinfo("Info", "Max 100 pdf pages for Claude inference")
                    #                 break
                    #             self.file_content.append({
                    #                 "type": "document",
                    #                 "source":{
                    #                     "type": "base64",
                    #                     "media_type": "application/pdf",
                    #                     "data": pdf_string.decode('utf-8'),
                    #                     },
                    #                 "title": f"{file_name}_page_{page_num + 1}",
                    #                 "citations": {"enabled": True},
                    #                 # "cache_control": {"type": "ephemeral"}
                    #             }
                    #             )
                    #     output_pdf.close()
                except Exception as e:
                    self.history.insert(tk.END, "Error: " + str(e) + '\n')
                pdf_document.close()
                self.history.insert(tk.END, f"\nPDF: {file_name}\n\n")


            # Video
            if mime_type[0:5] == 'video': 
                try:
                    # 获取视频文件格式
                    format = local_file.split('.')[-1].lower()
                    with open(local_file, "rb") as video_file:
                        binary_data = video_file.read()
                        base_64_encoded_data = base64.b64encode(binary_data)
                        self.file_content.append({
                            "video": {
                                "format": format,
                                "source": {
                                    "bytes": base_64_encoded_data.decode('utf-8')
                                }
                            }
                            })
                except Exception as e:
                    self.history.insert(tk.END, "Error: " + str(e) + '\n')
                self.history.insert(tk.END, f"\nVideo: {file_name}\n\n")

            self.history.see(tk.END)
        return

    # Save System Prompt
    def save_sys_prompt(self):
        prompt_title = self.sys_prompt_var.get()
        system_prompt = self.instruction_text.get("1.0", tk.END).strip()
        sys_prompt_dict[prompt_title] = system_prompt
        with open(sys_prompt_path, "w", encoding="utf-8") as f:
            json.dump(sys_prompt_dict, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Info", f"System prompt '{prompt_title}' saved to {sys_prompt_path}")
        self.entry.focus_set()
        return

    # Change Sys Prompt
    def change_sysprompt(self, event=None):
        prompt_title = self.sys_prompt_var.get()
        self.instruction_text.delete("1.0", tk.END)
        self.instruction_text.insert(tk.END, sys_prompt_dict[prompt_title])
        self.entry.focus_set()
        return

    def new_sys_prompt(self, event=None):
        prompt_title = simpledialog.askstring("New System Prompt", "Enter a title for the new system prompt:")
        if prompt_title is not None:
            sys_prompt_dict[prompt_title] = ""
            self.sys_prompt_list = list(sys_prompt_dict.keys())
            self.sys_prompt_var.set(prompt_title)
            self.sys_prompt_menu['values'] = self.sys_prompt_list
            self.instruction_text.delete("1.0", tk.END)
            self.instruction_text.focus_set()
        return
    
    def del_sys_prompt(self, event=None):
        prompt_title = self.sys_prompt_var.get()
        if prompt_title in sys_prompt_dict:
            confirm = messagebox.askyesno("Delete System Prompt", f"Are you sure you want to delete the system prompt '{prompt_title}'?")
            if confirm: 
                del sys_prompt_dict[prompt_title]
                with open(sys_prompt_path, "w", encoding="utf-8") as f:
                    json.dump(sys_prompt_dict, f, indent=2, ensure_ascii=False)
                self.sys_prompt_list = list(sys_prompt_dict.keys())
                self.sys_prompt_var.set(self.sys_prompt_list[0])
                self.sys_prompt_menu['values'] = self.sys_prompt_list
                self.change_sysprompt()

        else:
            messagebox.showerror("Error", f"System prompt '{prompt_title}' not found")
        return

    def check_remember_history(self, event=None):
        if self.remember_history.get() == False:
            self.clear_history()



# Main
if __name__ == '__main__':
    set_profile()
    logger.info("Starting... logging to ./bedrock_chatapp_history.log")
    root = tk.Tk()
    app = ChatApp(root)
    try:
        root.mainloop()
    finally:
        app.cleanup()
