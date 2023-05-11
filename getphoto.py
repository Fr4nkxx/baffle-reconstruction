# -*- coding: utf-8 -*-
"""
Created on Fri Jun 10 12:15:18 2022

@author: A410-2
"""


import sys
import cv2
import os

sys.path.append("/opt/MVS/Samples/64/Python/MvImport")
from MvCameraControl_class import *

def init_device():
    """
    ch:初始化设备 | en:init device
    nTLayerType [IN] 枚举传输层 ，pstDevList [OUT] 设备列表
    """
    # 获得设备信息
    deviceList = MV_CC_DEVICE_INFO_LIST()
    tlayerType = MV_GIGE_DEVICE
    
    ret = MvCamera.MV_CC_EnumDevices(tlayerType, deviceList)

    if ret != 0:
        print("enum devices fail! ret[0x%x]" % ret)
        sys.exit()

    if deviceList.nDeviceNum == 0:
        print("find no device!")
        sys.exit()

    print("Find %d devices!" % deviceList.nDeviceNum)

    for i in range(0, deviceList.nDeviceNum):
        mvcc_dev_info = cast(deviceList.pDeviceInfo[i], POINTER(MV_CC_DEVICE_INFO)).contents
        if mvcc_dev_info.nTLayerType == MV_GIGE_DEVICE:
            print("\ngige device: [%d]" % i)
            # 输出设备名字
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stGigEInfo.chModelName:
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)
            # 输出设备ID
            nip1 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0xff000000) >> 24)
            nip2 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x00ff0000) >> 16)
            nip3 = ((mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x0000ff00) >> 8)
            nip4 = (mvcc_dev_info.SpecialInfo.stGigEInfo.nCurrentIp & 0x000000ff)
            print("current ip: %d.%d.%d.%d\n" % (nip1, nip2, nip3, nip4))
        # 输出USB接口的信息
        elif mvcc_dev_info.nTLayerType == MV_USB_DEVICE:
            print("\nu3v device: [%d]" % i)
            strModeName = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chModelName:
                if per == 0:
                    break
                strModeName = strModeName + chr(per)
            print("device model name: %s" % strModeName)

            strSerialNumber = ""
            for per in mvcc_dev_info.SpecialInfo.stUsb3VInfo.chSerialNumber:
                if per == 0:
                    break
                strSerialNumber = strSerialNumber + chr(per)
            print("user serial number: %s" % strSerialNumber)
    return deviceList

def select_cam(deviceList,nConnectionNum):
    # ch:创建相机实例 | en:Creat Camera Object
    cam = MvCamera()

    # ch:选择设备并创建句柄 | en:Select device and create handle
    # cast(typ, val)，这个函数是为了检查val变量是typ类型的，但是这个cast函数不做检查，直接返回val
    stDeviceList = cast(deviceList.pDeviceInfo[int(nConnectionNum)], POINTER(MV_CC_DEVICE_INFO)).contents

    ret = cam.MV_CC_CreateHandle(stDeviceList)
    if ret != 0:
        print("create handle fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:打开设备 | en:Open device
    ret = cam.MV_CC_OpenDevice(MV_ACCESS_Exclusive, 0)
    if ret != 0:
        print("open device fail! ret[0x%x]" % ret)
        sys.exit()

    # ch:探测网络最佳包大小(只对GigE相机有效) | en:Detection network optimal package size(It only works for the GigE camera)
    if stDeviceList.nTLayerType == MV_GIGE_DEVICE:
        nPacketSize = cam.MV_CC_GetOptimalPacketSize()
        if int(nPacketSize) > 0:
            ret = cam.MV_CC_SetIntValue("GevSCPSPacketSize", nPacketSize)
            if ret != 0:
                print("Warning: Set Packet Size fail! ret[0x%x]" % ret)
        else:
            print("Warning: Get Packet Size fail! ret[0x%x]" % nPacketSize)

    # ch:设置触发模式\曝光模式\增益模式 | en:Set trigger mode
    ret = cam.MV_CC_SetEnumValue("ExposureAuto", 2)
    if ret != 0:
        print("Set ExposureAuto fail! ret[0x%x]" % ret)
        sys.exit()
    
    ret = cam.MV_CC_SetEnumValue("GainAuto", MV_GAIN_MODE_CONTINUOUS)
    if ret != 0:
        print("Set GainAuto fail! ret[0x%x]" % ret)
        sys.exit()

    ret = cam.MV_CC_SetEnumValue("TriggerMode", MV_TRIGGER_MODE_OFF)
    if ret != 0:
        print("set trigger mode fail! ret[0x%x]" % ret)
        sys.exit()


    # ch:获取数据包大小 | en:Get payload size
    stParam = MVCC_INTVALUE()
    memset(byref(stParam), 0, sizeof(MVCC_INTVALUE))
    # MV_CC_GetIntValue，获取Integer属性值，handle [IN] 设备句柄
    # strKey [IN] 属性键值，如获取宽度信息则为"Width"
    # pIntValue [IN][OUT] 返回给调用者有关相机属性结构体指针
    # 得到图片尺寸，这一句很关键
    # payloadsize，为流通道上的每个图像传输的最大字节数，相机的PayloadSize的典型值是(宽x高x像素大小)，此时图像没有附加任何额外信息
    ret = cam.MV_CC_GetIntValue("PayloadSize", stParam)
    if ret != 0:
        print("get payload size fail! ret[0x%x]" % ret)
        sys.exit()

    nPayloadSize = stParam.nCurValue

    return cam, nPayloadSize

def get_image(cam, nPayloadSize, devicenum):
    """
    获取图像
    :param cam:
    :param nPayloadSize:
    :return: image
    """
    # ch:开始取流 | en:Start grab image
    ret = cam.MV_CC_StartGrabbing()
    # 返回获取图像缓存区
    data_buf = (c_ubyte * nPayloadSize)()
    # 输出帧的信息
    stFrameInfo = MV_FRAME_OUT_INFO_EX()
    # 将帧信息全部清空
    memset(byref(stFrameInfo), 0, sizeof(stFrameInfo))
    # 采用超时机制获取一帧图片，SDK内部等待直到有数据时返回，成功返回0
    ret = cam.MV_CC_GetOneFrameTimeout(byref(data_buf), nPayloadSize, stFrameInfo, 10000)
    if ret == 0:
        #print("get one frame: Width[%d], Height[%d], nFrameNum[%d]" % (stFrameInfo.nWidth, stFrameInfo.nHeight, stFrameInfo.nFrameNum))
        nRGBSize = stFrameInfo.nWidth * stFrameInfo.nHeight * 3
        stConvertParam=MV_SAVE_IMAGE_PARAM_EX()
        stConvertParam.nWidth = stFrameInfo.nWidth
        stConvertParam.nHeight = stFrameInfo.nHeight
        stConvertParam.pData = data_buf
        stConvertParam.nDataLen = stFrameInfo.nFrameLen
        stConvertParam.enPixelType = stFrameInfo.enPixelType
        stConvertParam.nImageLen = stConvertParam.nDataLen
        stConvertParam.nJpgQuality = 70
        stConvertParam.enImageType = MV_Image_Jpeg
        stConvertParam.pImageBuffer = (c_ubyte * nRGBSize)()
        stConvertParam.nBufferSize = nRGBSize
        ret = cam.MV_CC_SaveImageEx2(stConvertParam)
        if ret != 0:
            print ("convert pixel fail ! ret[0x%x]" % ret)
            del data_buf
            sys.exit()
        file_path = "./Data/image/image_buff"+str(devicenum)+".jpg"
        file_open = open(file_path.encode('ascii'), 'wb+')
        try:
            img_buff = (c_ubyte * stConvertParam.nDataLen)()
            memmove(byref(img_buff), stConvertParam.pImageBuffer, stConvertParam.nDataLen)
            file_open.write(img_buff)
        except Exception as e:
            raise Exception("save file executed failed1::%s" % e)
        finally:
            file_open.close()
        '''
        image = (c_ubyte * stConvertParam.nImageLen)()
        cdll.msvcrt.memcpy(byref(image), stConvertParam.pImageBuffer, stConvertParam.nImageLen)
        file_open.write(image)
        '''
    return data_buf

def close_device(cam, data_buf):
    """
    关闭设备
    :param cam:
    :param data_buf:
    """
    # ch:停止取流 | en:Stop grab image
    ret = cam.MV_CC_StopGrabbing()
    if ret != 0:
        print("stop grabbing fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    # ch:关闭设备 | Close device
    ret = cam.MV_CC_CloseDevice()
    if ret != 0:
        print("close deivce fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    # ch:销毁句柄 | Destroy handle
    ret = cam.MV_CC_DestroyHandle()
    if ret != 0:
        print("destroy handle fail! ret[0x%x]" % ret)
        del data_buf
        sys.exit()

    del data_buf


if __name__ == "__main__":
    i = 27
    # 初始化设备
    deviceList = init_device()
    output_path = "./Data/image/rgb1"
    folder = os.path.exists(output_path)
    if not folder:
        os.makedirs(output_path) 
    cam_num = 1
    if cam_num == 1:
        cam1, nPayloadSize1 = select_cam(deviceList,0)
        while True:
            data_buf1 = get_image(cam1, nPayloadSize1, 1)
            image1 = cv2.imread("./Data/image/image_buff1.jpg")
            cv2.namedWindow("image1", 0)
            cv2.resizeWindow("image1", 2000, 1440)
            cv2.imshow("image1", image1)
            key_code = cv2.waitKey(20)
            if key_code == ord('p'):
                Img_Name1 = output_path + '%05d'% i + ".jpg"
                print(Img_Name1)
                cv2.imwrite(Img_Name1, image1)
                i = i+1
                continue
            elif key_code == ord('q'):
                break
        cv2.destroyAllWindows()
        close_device(cam1, data_buf1)
        
        
    if cam_num == 2:
        cam1, nPayloadSize1 = select_cam(deviceList,0)
        cam2, nPayloadSize2 = select_cam(deviceList,1)
        while True:
            data_buf1 = get_image(cam1, nPayloadSize1, 1)
            data_buf2 = get_image(cam2, nPayloadSize2, 2)
            image1 = cv2.imread("./Data/image/image_buff1.jpg")
            image2 = cv2.imread("./Data/image/image_buff2.jpg")
            cv2.namedWindow("image1", 0)
            cv2.resizeWindow("image1", 2000, 1440)
            cv2.imshow("image1", image1)
            cv2.namedWindow("image2", 0)
            cv2.resizeWindow("image2", 2000, 1440)
            cv2.imshow("image2", image2)
            key_code = cv2.waitKey(20)
            if key_code == ord('p'):
                Img_Name1 = output_path + '%05d'% i + ".jpg"
                print(Img_Name1)
                cv2.imwrite(Img_Name1, image1)
                i = i+1
                Img_Name2 = output_path + '%05d'% i + ".jpg"
                print(Img_Name2)
                cv2.imwrite(Img_Name2, image2)
                i = i+1
                continue
            elif key_code == ord('q'):
                break
        cv2.destroyAllWindows()
        close_device(cam1, data_buf1)
        close_device(cam2, data_buf2)
    
    
    
