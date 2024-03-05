# Bedrock-chatapp-gui

本地运行 GUI(python) 与 Amazon Bedrock 背后的多个大模型进行对话交互，例如 Claude 3(多模态), Titan, AI21, Cohere。会带上上次的对话记录，直到你点Clear清理。并且方便随时调整参数和系统提示词。

* 自动读取本地配置的 AWS Profile，可以选择切换
* 选择支持 Bedrock 的 Region 和模型
* 自动读取该模型对应的典型参数在右上角，可以手工调整，每单次对话都会调用修改后的参数
* 系统提示词在右下角，每次对话都会带上历史对话，直到你点 CLEAR HIS. 清理历史
* 所有历史对话都会记录到当前运行目录下的 bedrock_chatapp_history.log
* 注意：boto3 >= 1.34.55
* 可选：建议安装最新的Python 3.12 以及更新对应的 tk3.12

参考安装命令

```shell
brew install python@3.12   
brew install python-tk@3.12
pip install -r requirements.txt --break-system-packages
```

* Linux  

运行命令

```shell
git clone https://github.com/hawkey999/bedrock-chatapp-gui
python3 bedrock-chatapp-gui/bedrock-chatapp-gui.py
```

* Windows  

可以按上面步骤使用 python ，也可以到[这里](https://github.com/hawkey999/bedrock-chatapp-gui/releases)直接下载打包好的 .exe 文件运行

* IAM

如果以前没有用过 AWS CLI （命令行），则需要在 AWS IAM 中创建一个用户，然后把 Access Key 和 Secret Key 配置到本地的 AWS Profile 中，具体步骤可以参考[创建IAM User](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html#id_users_create_console)。注意，这个 IAM 用户需要有 Bedrock 的权限。首次运行本程序的时候，会提示你输入 Access Key 和 Secret Key ，以及所在的 Region，然后会自动创建一个本地的 AWS Profile。  
如果以前配置过 AWS CLI，则不会再提示配置，而是直接读取本地的 AWS Profile 运行。

![img](./img/img2.png)
