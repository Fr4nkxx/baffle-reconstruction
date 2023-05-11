# baffle-restruct
## SAM
- default or vit_h: [ViT-H SAM model](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth).
- vit_l: [ViT-L SAM model](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_l_0b3195.pth).
- vit_b: [ViT-B SAM model](https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth).

put SAM.pth in ./third-party/SAM

## HIKROBOT MVS
1. download [HIKROBOT MVS SDK](https://www.hikrobotics.com/cn/machinevision/service/download?module=0)

2. install x86.deb

3. nano ~/.zshrc


    export MVCAM_COMMON_RUNENV=/opt/MVS/lib
    export LD_LIBRARY_PATH=/opt/MVS/lib/64:/opt/MVS/lib/32:$LD_LIBRARY_PATH

4. Gige net setting:
- ipv4:192.168.1.2/24
- gateway:192.168.1.1

5. reboot