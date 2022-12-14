import os
import sys

sys.path.append(os.path.realpath("."))

from abc import ABC, abstractmethod
from utils import read_image, read_secret
import numpy as np
from sklearn.metrics import hamming_loss
from skimage.metrics import structural_similarity
import cv2


class Method(ABC):
    @abstractmethod
    def encrypt(self, carrier_path, secret_path, **args):
        pass

    @abstractmethod
    def decrypt(self, length, img, result_path, **args) -> str:
        pass

    def back_process(self, path, bits) -> str:
        with open(path, "wb") as f:
            for i in range(0, len(bits), 8):
                ascii_code = int(bits[i:i+8], 2)
                ascii_code = chr(ascii_code)

                b = bytes(ascii_code, encoding="utf-8")
                f.write(b)
        return bits
class Handler:
    def __init__(self, carrier_path, secret_path, result_path, method: Method=None) -> None:
        self._method = method

        self._img, self._shape = read_image.read_img_by_cv2(carrier_path)
        self._secret = read_secret.read_secret_bin(secret_path)
        self._length = len(self._secret)

        self._encrypted_img = None

        self._carrier_path = carrier_path
        self._secret_path = secret_path
        self._result_path = result_path
    
    @property
    def method(self):
        return self._method
    
    @method.setter
    def method(self, method: Method):
        self._method = method

    def PSNR(self):
        primary = np.array(
            self._img
        )

        encrypted = np.array(
            self._encrypted_img
        )

        MSE = np.mean(
            (primary - encrypted) ** 2
        )

        if MSE == 0:
            psnr = float('inf')
        else:
            psnr = 20 * np.log10(
                255 / np.sqrt(MSE)
            )

        # print("PSNR：", psnr)

        # if psnr >= 50:
        #     print("加密前后图像误差极小")
        # elif psnr >= 30:
        #     print("难以察觉加密前后图像的误差")
        # elif psnr >= 20:
        #     print("人眼可以察觉加密前后图像误差")
        # elif psnr >= 10:
        #     print("存在明显的图像差异，但仍可判断为可能是同一张图片")
        # else:
        #     print("压根就不是同一张图")

        return psnr

    def SSIM(self):
        ssim = structural_similarity(self._img, self._encrypted_img)
        
        # print("SSIM：", ssim)

        return ssim

    def Hamming(self, decrypted):
        res = hamming_loss(np.array(
            [
                int(x) for x in self._secret
            ]
        ), np.array(
            [
                int(x) for x in decrypted
            ]
        ))
        return res

    def run(self, **args):
        interval_step = args["interval_step"] if "interval_step" in args else 0
        check_size =  args["check_size"] if "check_size" in args else 0
        encrypted_img = self._method().encrypt(
            carrier_path=self._carrier_path,
            secret_path=self._secret_path,
            interval_step=interval_step,
            check_size=check_size
        )
        cv2.imwrite(self._result_path, encrypted_img, [cv2.IMWRITE_JPEG_QUALITY, 89])

        self._encrypted_img, shape = read_image.read_img_by_cv2(self._result_path)

        # if self._shape != shape:
        #     print("图片尺寸不一致")

        psnr = self.PSNR()
        ssim = self.SSIM()

        bits = self._method().decrypt(
            self._length, 
            encrypted_img,
            "./decrypted.py",
            interval_step=interval_step,
            check_size=check_size
        )
        hamming = self.Hamming(bits)

        if hamming == 0:
            # print("解密结果完全一致")
            pass
        else:
            # print(hamming)
            pass

        return psnr, ssim, hamming