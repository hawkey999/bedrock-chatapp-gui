import boto3, botocore, json, os, logging
import tkinter as tk
from tkinter import ttk, Label, Scrollbar, Text, Button, font
import threading
import queue
import configparser
os.environ['OS_ACTIVITY_DT_MODE'] = 'disable' 

# default values
default_intruction = "Answer the QUESTION, and consider the history conversation in CONTEXT, if no context or no valuable info in the context, just directly answer the question."
MAX_RETRIES = 3 
accept = 'application/json'
contentType = 'application/json'

def get_regions():
    return ('us-east-1', 'us-west-2', 'ap-southeast-1', 'ap-northeast-1')

def get_modelIds():
    return ('anthropic.claude-v2', 'anthropic.claude-instant-v1', 'anthropic.claude-v1', 'amazon.titan-embed-text-v1', 'amazon.titan-text-express-v1', 'cohere.command-text-v14', 'ai21.j2-mid-v1', 'ai21.j2-ultra-v1')

default_para = {                            # 可以在运行之后的界面上修改
    "anthropic.claude-v2": {
        "max_tokens_to_sample": 8*1024-1,   # 最大输出的Token数量是8K，最大输入不需要填写，Claude默认100K
        "temperature": 0.5,                 # Use a lower value to decrease randomness in the response. Claude 0-1, default 0.5
        "top_k": 250,                       # Use a lower value to ignore less probable options.  Claude 0-500, default 250
        "top_p": 1,                         # Specify the number of token choices the model uses to generate the next token. Claude 0-1, default 1
        "stop_sequences": ["\\n\\nHuman:"],
        },    
    "anthropic.claude-instant-v1": {
        "max_tokens_to_sample": 8*1024-1, 
        "temperature": 0.5,
        "top_k": 250,
        "top_p": 1,
        },
    "anthropic.claude-v1": {
        "max_tokens_to_sample": 8*1024-1, 
        "temperature": 0.5,
        "top_k": 250,
        "top_p": 1,
        },
    "amazon.titan-embed-text-v1": {
    },
    "amazon.titan-text-express-v1": {
        "maxTokenCount": 8192,
        "stopSequences": [],
        "temperature":0,
        "topP":1
    },
    "cohere.command-text-v14": {
        "max_tokens": 100,
        "temperature": 0.8
    },
    "ai21.j2-mid-v1": {
        "maxTokens": 200,
        "temperature": 0,
        "topP": 1,
        "countPenalty": {"scale": 0},
        "presencePenalty": {"scale": 0},
        "frequencyPenalty": {"scale": 0}
    },
    "ai21.j2-ultra-v1": {
        "maxTokens": 200,
        "temperature": 0,
        "topP": 1,
        "countPenalty": {"scale": 0},
        "presencePenalty": {"scale": 0},
        "frequencyPenalty": {"scale": 0}
    },
}

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('./bedrock_chatapp_history.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s', datefmt='%Y%m%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_profiles():
    config = configparser.ConfigParser()
    config.read(os.path.expanduser('~/.aws/credentials'))
    return config.sections()

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AWS Bedrock ChatApp(TK GUI) - by James Huang")
        self.root.geometry('1200x726')
        # Set the column and row weights
        self.root.grid_columnconfigure(0, weight=4)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=0)
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_rowconfigure(2, weight=0)
        custom_font = font.Font(size=14)

        # Create a frame for the profile and region selectors
        selector_frame = tk.Frame(root)
        selector_frame.grid(row=0, column=0, padx=5, pady=5, sticky='w')

        Label(selector_frame, text="AWS Profile: ").pack(side=tk.LEFT)
        profiles = get_profiles()
        self.profile_var = tk.StringVar()
        self.profile_var.set(profiles[0] if profiles else "No Profile Found")
        self.profile_menu = ttk.Combobox(selector_frame, width=10, textvariable=self.profile_var, values=profiles)
        self.profile_menu.pack(side=tk.LEFT)
        self.profile_menu.bind("<<ComboboxSelected>>", self.change_profile_region)

        Label(selector_frame, text="Bedrock Region: ").pack(side=tk.LEFT)
        regions = get_regions()
        self.region_var = tk.StringVar()
        self.region_var.set(regions[0] if regions else "No Region Found")
        self.region_menu = ttk.Combobox(selector_frame, width=10, textvariable=self.region_var, values=regions)
        self.region_menu.pack(side=tk.LEFT)
        self.region_menu.bind("<<ComboboxSelected>>", self.change_profile_region)

        Label(selector_frame, text="ModelId: ").pack(side=tk.LEFT)
        modelIds = get_modelIds()
        self.modelId_var = tk.StringVar()
        self.modelId_var.set(modelIds[0] if modelIds else "No ModelId Found")
        self.modelId_menu = ttk.Combobox(selector_frame, width=20, textvariable=self.modelId_var, values=modelIds)
        self.modelId_menu.pack(side=tk.LEFT)
        self.modelId_menu.bind("<<ComboboxSelected>>", self.change_modelId)

        Label(selector_frame, text="Font: ").pack(side=tk.LEFT)
        fontSize = ('8', '10', '12', '14', '16', '18', '20', '22', '24', '26', '28')
        self.fontSize_var = tk.StringVar()
        self.fontSize_var.set(fontSize[3] if fontSize else "No Font Found")
        self.fontSize_menu = ttk.Combobox(selector_frame, width=5, textvariable=self.fontSize_var, values=fontSize)
        self.fontSize_menu.pack(side=tk.LEFT)
        self.fontSize_menu.bind("<<ComboboxSelected>>", self.change_fontSize)

        lable_frame = tk.Frame(root)
        lable_frame.grid(row=0, column=1, padx=5, pady=5, sticky='w')
        Label(lable_frame, text="Inference Para: ").pack(side=tk.LEFT)

        # Create a frame for the text history and scrollbar
        history_frame = tk.Frame(root)
        history_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
        history_frame.grid_columnconfigure(0, weight=1)
        history_frame.grid_rowconfigure(0, weight=1)

        self.scrollbar = Scrollbar(history_frame)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history = Text(history_frame, font=custom_font, yscrollcommand=self.scrollbar.set)
        self.history.pack(fill=tk.BOTH, expand=True)

        self.scrollbar.config(command=self.history.yview)
        
        # Create a frame for the bedrock_para JSON text and scrollbar
        bedrock_para_frame = tk.Frame(root)
        bedrock_para_frame.grid(row=1, column=1, padx=5, pady=5, sticky='nsew')
        bedrock_para_frame.grid_columnconfigure(0, weight=1)
        bedrock_para_frame.grid_rowconfigure(0, weight=1)
        bedrock_para_frame.grid_rowconfigure(1, weight=1)        

        self.bedrock_para = tk.StringVar()
        self.bedrock_para.set(json.dumps(default_para, indent=1)) 
        self.bedrock_para_text = Text(bedrock_para_frame, font=custom_font, width=15)
        self.bedrock_para_text.insert(tk.END, self.bedrock_para.get())
        self.bedrock_para_text.grid(row=0, column=0, sticky='nsew')

        self.instruction_var = tk.StringVar()
        self.instruction_var.set(default_intruction)
        self.instruction_text = Text(bedrock_para_frame, font=custom_font, width=15)
        self.instruction_text.insert(tk.END, default_intruction)
        self.instruction_text.grid(row=1, column=0, sticky='nsew')


        # Create a frame for the input and buttons
        input_frame = tk.Frame(root)
        input_frame.grid(row=2, column=0, padx=5, pady=5, sticky='ew')
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=0)

        self.entry = Text(input_frame, height=4, font=custom_font)
        self.entry.pack(fill=tk.X, expand=True, side=tk.LEFT)
        self.entry.bind("<Shift-Return>", self.just_enter)
        self.entry.bind("<Command-Return>", self.just_enter)
        self.entry.bind("<Return>", self.send_message)
        self.entry.focus_set()

        button_frame = tk.Frame(root)
        button_frame.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
        button_frame.grid_columnconfigure(0, weight=0)
        button_frame.grid_rowconfigure(0, weight=1)

        self.send_button = Button(button_frame, text="Send", command=self.send_message, width=8)
        self.send_button.grid(row=0, column=0, sticky='ew')
        self.clear_button = Button(button_frame, text="Clear", command=self.clear_history, width=8)
        self.clear_button.grid(row=1, column=0, sticky='ew')
        self.history_num = Label(button_frame, text="History: 0")
        self.history_num.grid(row=1, column=2, sticky='ew')

        self.change_profile_region()
        self.change_modelId()
        self.chat_history = []
        self.queue = queue.Queue()
        self.root.after(200, self.check_queue)

    def change_profile_region(self, event=None):
        self.profile = self.profile_var.get()
        self.region = self.region_var.get()

    def change_modelId(self, event=None):
        self.modelId = self.modelId_var.get()
        self.bedrock_para_text.delete("1.0", tk.END)
        self.bedrock_para_text.insert(tk.END, json.dumps(default_para[self.modelId], indent=1))

    def change_fontSize(self, event=None):
        self.fontSize = self.fontSize_var.get()
        self.custom_font = font.Font(size=int(self.fontSize))
        self.history.config(font=self.custom_font)
        self.entry.config(font=self.custom_font)
        self.bedrock_para_text.config(font=self.custom_font)
        self.instruction_text.config(font=self.custom_font)

    def save_history(self, history_record):     
        self.chat_history.append(history_record)
        self.history_num.config(text=f"History: {len(self.chat_history)}")

    def just_enter(self, event=None):
        return

    # 发送消息按钮
    def send_message(self, event=None):
        try:
            # Pause input and send button
            self.send_button.config(state=tk.DISABLED)
            self.entry.unbind("<Return>")

            # Construct context
            context = json.dumps(self.chat_history)
            question = self.entry.get("1.0", tk.END).strip()
            self.history.insert(tk.END, "You: " + question + '\n\n')
            self.history.see(tk.END)
            history_record = f"History Question: {question}\n"
            self.save_history(history_record)
            logger.info(history_record)

            # 这里修改默认的 Promot 模版
            instruction = self.instruction_text.get("1.0", tk.END).strip()
            prompt = f"""\n\nHuman: "{instruction}"\n
                        CONTEXT: "{context}"\n
                        QUESTION: "{question}"\n
                        Assistant:"""
            # 部分模型不需要 CONTEXT，直接输出 QUESTION
            if self.modelId.startswith("amazon.titan-embed-text"):
                prompt = question

            self.history.insert(tk.END, f"Bot({self.modelId}): ")
            self.history.see(tk.END)

            # Construct bedrock_para
            bedrock_para = json.loads(self.bedrock_para_text.get("1.0", tk.END).strip())
            if self.modelId.startswith("anthropic.claude"):
                bedrock_para['prompt'] = prompt
            elif self.modelId.startswith("amazon.titan"):
                bedrock_para['inputText'] = prompt
            elif self.modelId.startswith("cohere.command"):
                bedrock_para['prompt'] = prompt
            elif self.modelId.startswith("ai21.j2"):
                bedrock_para['prompt'] = prompt

            invoke_body = json.dumps(bedrock_para)
            # 异步调用Bedrock API
            threading.Thread(target=self.generate_reply, args=(invoke_body,)).start()
            self.entry.delete("1.0", tk.END)
        except Exception as e:
            self.history.insert(tk.END, "Error instruction: " + str(e) + '\n')
        return "break"

    # 清理历史消息，后面的对话将不会考虑Clear之前的历史上下文
    def clear_history(self):
        answers = "\n------Clean Conversatioin------\n"
        self.queue.put(answers)
        logger.info(answers)
        self.chat_history = []
        self.history_num.config(text=f"History: {len(self.chat_history)}")

    # 异步调用Bedrock API
    def generate_reply(self, invoke_body):
        answers = ""
        try:
            # Invoke streaming model
            session = boto3.Session(profile_name=self.profile)
            config = botocore.config.Config(retries={'max_attempts': MAX_RETRIES})
            self.client = session.client("bedrock-runtime", region_name=self.region, config=config)
        
            if self.modelId.startswith("anthropic.claude"):
                response = self.client.invoke_model_with_response_stream(body=invoke_body, modelId=self.modelId, accept=accept, contentType=contentType)
                for event in response['body']:
                    chunk_str = json.loads(event['chunk']['bytes'].decode('utf-8'))
                    answer = chunk_str.get('completion')
                    self.queue.put(answer)
                    answers += answer
            
            # Invoke non-streaming model
            else:
                response = self.client.invoke_model(body=invoke_body, modelId=self.modelId, accept=accept, contentType=contentType)
                response_body = json.loads(response.get('body').read())
            if self.modelId.startswith("amazon.titan-embed"):
                answers = json.dumps(response_body.get('embedding'))
                self.queue.put(answers)
            elif self.modelId.startswith("cohere.command-text"):
                for answer in response_body.get('generations'):
                    answers += answer.get('text')
                self.queue.put(answers)
            elif self.modelId.startswith("ai21.j2"):
                for answer in response_body.get('completions'):
                    answers += answer.get('data').get('text')
                self.queue.put(answers)
        except Exception as e:
            self.queue.put(f"\n\nException Error: {str(e)}\n")
        
        history_record = f"History Answer: {answers}\n---END---\n"
        self.save_history(history_record)
        logger.info(history_record)
        self.queue.put("\n---END---\n\n")
        self.send_button.config(state=tk.NORMAL)
        self.entry.bind("<Return>", self.send_message)
        return

    # 异步打印Bedrock返回消息
    def check_queue(self):
        while not self.queue.empty():
            answer = self.queue.get()
            self.history.insert(tk.END, answer)
            self.history.see(tk.END)
        self.root.after(200, self.check_queue)


# Main
if __name__ == '__main__':
    logger.info("Starting... logging to ./bedrock_chatapp_history.log")
    root = tk.Tk()
    app = ChatApp(root)
    root.mainloop()
