## 针对ui3_1的环境，主要要做的如下：
### 1.下载安装 Poppler for Windows（PDF）
  找到最新版本的 poppler-xx_xx_xx-Release.zip，下载并解压到一个位置：
  https://github.com/oschwartz10612/poppler-windows/releases/
  解压后记得配置环境变量（bin目录下的地址）
### 2.下载安装 Tesseract OCR（图片）
  到官方地址下载 Windows 安装包，名为 tesseract-ocr-w64-setup-xxx.exe ： 
  https://github.com/tesseract-ocr/tesseract/releases
  安装后记得环境变量（安装地址）。
  #### 搞好后可能还是没办法识别图片中的中文，加上这个下载简体中文语言包文件：
  https://github.com/tesseract-ocr/tessdata/blob/main/chi_sim.traineddata?raw=true
![image](https://github.com/user-attachments/assets/034d2b41-4dd7-42af-b942-96de5dead10e)
现在可以成功上传word、pdf和图片并正确识别其中文字。
