import  readline
import qrcode
from PIL import Image
import os

def Create_Qrcode(strings,path,logo=""):
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=1,
    )

    with open('test.txt','r') as fr:
        for lines in fr.readlines():
            lines = lines.replace("\n","").strip()
            ID = lines
            lines = strings + lines
            if len(lines) > 0:
                qr.add_data(lines)
                qr.make(fit=True)
                img = qr.make_p_w_picpath()
                img = img.convert("RGBA")
                if os.path.exists(path) and os.path.isfile(logo):
                    icon = Image.open(logo)
                    img_w,img_h = img.size
                    factor = 5
                    size_w = int(img_w / factor)
                    size_h = int(img_h / factor)

                    icon_w, icon_h = icon.size
                    if icon_w > size_w:
                        icon_w = size_w
                    if icon_h > size_h:
                        icon_h = size_h
                    icon = icon.resize((icon_w,icon_h),Image.ANTIALIAS)
                    w = int((img_w - icon_w) / 2)
                    h = int((img_h - icon_h) / 2)
                    icon = icon.convert("RGBA")
                    img.paste(icon,(w,h),icon)

                    img.save( ID + '.jpg')

if __name__ == "__main__":
    Create_Qrcode('http://hepaidai.com/?channel_code=hpd&sub_id=','E:\PythonProject\\test','E:\PythonProject\\test\hpd.jpg')

# 说明:
# 需要安装第三方库：qrcode ,PIL , Image (推荐使用pip安装)
# strings： 二维码字符串
# path: 生成的二维码保存路径
# logo: 要添加的logo文件