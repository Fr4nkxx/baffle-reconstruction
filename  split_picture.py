from segment_anything import SamPredictor, sam_model_registry
import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import glob
import torch

def draw_circle(event, x, y, flags, param):
    global flag_mouse_lbutton_down, x1, y1, image,x2,y2
    if event == cv2.EVENT_LBUTTONDOWN:
        flag_mouse_lbutton_down = True
        x1 = x
        y1 = y
        cv2.circle(image, (x, y), 1, (0, 0, 255), thickness=2)
        print(x1,y1)
    if event == cv2.EVENT_LBUTTONUP:
        x2 = x
        y2 = y
        flag_mouse_lbutton_down = False
        cv2.rectangle(image, (x1, y1), (x, y), (0, 0, 255), 4)
        print(x2,y2)
    if event == cv2.EVENT_MOUSEMOVE and flags == cv2.EVENT_FLAG_LBUTTON:
        image[:] = temp_image
        cv2.rectangle(image, (x1, y1), (x, y), (0, 0, 255), 4)


if __name__ == '__main__':
    DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    imgs_path = glob.glob('/home/a410/Documents/Data/pic/baffle/rgb4/*.jpg')
    imgs_path.sort()
    output_path = '/home/a410/Documents/Data/pic/baffle/imgwithmask/'
    if not output_path:
        os.makedirs(output_path) 
    i = 6
    while i < len(imgs_path):
        img_dir = imgs_path[i]
        image = cv2.imread(img_dir)
        temp_image = image.copy()
        x1 = -1
        y1 = -1
        x2 = -1
        y2 = -1
        cv2.namedWindow("image",0)
        cv2.setMouseCallback("image",draw_circle)
        while True:
            cv2.imshow("image", image)
            if cv2.waitKey(10) == ord("n"):
                break

        boxes_point = np.array([[x1,y1,x2,y2]])
        print('segment anythings use '+str(DEVICE)+'......')
        sam = sam_model_registry["vit_h"](checkpoint="./third_party/SAM/sam_vit_h_4b8939.pth")
        sam.to(device=DEVICE)
        predictor = SamPredictor(sam)
        predictor.set_image(image,"BGR")
        if x1 == x2 and y1==y2:
            point_coords = np.array([[x1,y1]])
            masks, _, _ = predictor.predict(point_coords=point_coords,point_labels=np.array([1]),multimask_output=False)
        else:
            masks, _, _ = predictor.predict(box = boxes_point,multimask_output=False)
        res = image
        res[:,:,:][masks[0,:,:]==False] = 255
        cv2.namedWindow("imagewithmask",0)
        cv2.imshow('imagewithmask',res)

        print('-----Finish Split image['+ str(i) + ']-----')
        while True:
            if cv2.waitKey(10) == ord("n"):
                print('next image:')
                cv2.imwrite(output_path+img_dir[-9:],res)
                i = i + 1
                break
            elif cv2.waitKey(10) == ord("g"):
                print('again image:')
                break
    cv2.destroyAllWindows()
