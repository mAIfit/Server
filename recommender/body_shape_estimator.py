import sys

sys.path.append("/home/myungjune/projects/multiperson")
sys.path.append("/home/myungjune/projects/multiperson/YOLOv4")

import os

os.environ[
    "PYOPENGL_PLATFORM"
] = "osmesa"  # set osmesa as render backend for use in SSH

import torch

import cv2
import numpy as np
import argparse

from YOLOv4.tool.utils import load_class_names
from YOLOv4.tool.torch_utils import do_detect
from lib.utils.img_utils import split_boxes_cv2
from lib.utils.model_utils import create_all_network
from lib.utils.input_utils import (
    get_pose_estimator_input,
    get_feature_extractor_input,
    get_ik_input,
)
from lib.utils.renderer import Renderer
from lib.utils.file_utils import update_config, make_folder
from lib.utils.output_utils import (
    save_3d_joints,
    save_2d_joints,
    process_output,
    save_mesh_obj,
    save_mesh_rendering,
    save_mesh_pkl,
)


class BodyShapeEstimator:
    def __init__(self):
        """
        load MultiPerson model
        """
        config_path = "/home/myungjune/projects/multiperson/configs/demo.yaml"

        self.demo_cfg = update_config(config_path)
        self.namesfile = self.demo_cfg.YOLO.namesfile
        self.height = self.demo_cfg.YOLO.target_height
        self.width = self.demo_cfg.YOLO.target_width
        self.n_classes = self.demo_cfg.YOLO.n_classes

        self.FLAGS = self.demo_cfg.PoseEstimator.FLAGS
        self.max_num_person = self.demo_cfg.SmplTR.max_num_person

        (
            self.yolo,
            self.pose_estimator,
            self.ik_net,
            self.feature_extractor,
            self.smpl_layer,
            self.smplTR,
        ) = create_all_network(self.demo_cfg)

        print("init success")

    def estimate(self, imgfile, betas_only=False):
        """
        Input:
         - image: image path
        Output:
         - betas: python list of float body shape parameters (10,)
         - meshed_image: path to mesh of given image (Optional: if betas_only is True, return None)
        """

        split_images_folder, pose_results_folder, mesh_results_folder = make_folder(
            self.demo_cfg, imgfile
        )

        orig_img = cv2.imread(imgfile)
        orig_height, orig_width = orig_img.shape[:2]
        renderer = Renderer(
            smpl=self.smpl_layer, resolution=(orig_width, orig_height), orig_img=True
        )

        yolo_input_img = cv2.resize(orig_img, (self.width, self.height))
        yolo_input_img = cv2.cvtColor(yolo_input_img, cv2.COLOR_BGR2RGB)

        for i in range(2):
            boxes = do_detect(self.yolo, yolo_input_img, 0.4, 0.6, use_cuda=False)

        class_names = load_class_names(self.namesfile)
        img_patch_list, refined_boxes, trans_invs = split_boxes_cv2(
            orig_img, boxes[0], split_images_folder, class_names
        )
        refined_boxes = np.array(refined_boxes)

        num_person = len(img_patch_list)
        num_person = min(num_person, self.max_num_person)
        if num_person < 1: 
            return None # person not found

        feature_dump = torch.zeros(1, self.max_num_person, 2048).float()
        rot6d_dump = torch.zeros(1, self.max_num_person, 24, 6).float()
        betas_dump = torch.zeros(1, self.max_num_person, 10).float()

        for person_id, img_patch in enumerate(img_patch_list[:num_person]):
            img_plot, img_pe_input, intrinsic = get_pose_estimator_input(
                img_patch, self.FLAGS
            )

            with torch.no_grad():
                j2d, j3d, j3d_abs, skeleton_indices, edges = self.pose_estimator(
                    img_pe_input, intrinsic, intrinsic
                )

            save_3d_joints(j3d_abs, edges, pose_results_folder, person_id)
            save_2d_joints(img_plot, j2d, edges, pose_results_folder, person_id)

            img_ik_input = get_ik_input(img_patch, self.demo_cfg, self.FLAGS)
            j3ds_abs_meter = j3d_abs / 1000
            ik_net_output = self.ik_net(img_ik_input, j3ds_abs_meter)
            rot6d_ik_net = ik_net_output.pred_rot6d

            betas_ik_net = ik_net_output.pred_shape
            if betas_only:
                # os.chdir(old_cwd)
                return {"betas": betas_ik_net[0].tolist(), "meshed_image": None}

            img_fe_input = get_feature_extractor_input(img_patch)
            img_feature = self.feature_extractor.extract(img_fe_input)

            feature_dump[0][person_id] = img_feature[0]
            rot6d_dump[0][person_id] = rot6d_ik_net[0]
            betas_dump[0][person_id] = betas_ik_net[0]

        angle = 6.5
        axis = "x"
        refined_rot6d, refined_betas, refined_cam = self.smplTR(
            feature_dump, rot6d_dump, betas_dump
        )
        axis_angle, rot6d, betas, cam, verts, faces = process_output(
            self.smpl_layer,
            refined_rot6d,
            refined_betas,
            refined_cam,
            rotation_angle=angle,
            rotation_axis=axis,
        )

        meshed_image_name = save_mesh_rendering(
            renderer,
            verts,
            refined_boxes,
            cam,
            orig_height,
            orig_width,
            num_person,
            mesh_results_folder,
            rotation_angle=angle,
            rotation_axis=axis,
        )

        return {"betas": betas_ik_net[0].tolist(), "meshed_image": meshed_image_name}

    def extract_betas(self, image):
        """
        Input:
         - image: image path
        Output:
         - betas: python list of float body shape parameters (10,)
        """
        return self.estimate(image, betas_only=True)["betas"]

    def extract_mesh(self, image):
        """
        Generates mesh from given image.
        Store the mesh in a .jpg file and return the path to the mesh.

        Input:
         - image: image path
        Output:
         - mesh_path: path to mesh of given image
        """
        return self.estimate(image, betas_only=False)["meshed_image"]

    def extract_betas_and_mesh(self, image):
        """
        Generates mesh from given image.
        Store the mesh in a .jpg file and return the path to the mesh.

        Input:
         - image: image path
        Output:
         - betas: python list of float body shape parameters (10,)
         - mesh_path: path to mesh of given image
        """
        return self.estimate(image, betas_only=False)


def main():
    # single image case
    # img_paths = ['/home/myungjune/projects/multiperson/demo_image/6.jpg']

    # multiple image case
    reviews_obj = [
        {
            "content": "핏도 예쁘고 따뜻하기도 해요 기본템으로 강추드립니다!",
            "gender": "M",
            "height": "179",
            "weight": "81",
            "product_size": "L",
            "image": "/home/myungjune/projects/maifit-server/temp/3c99136f-61a3-42c3-aca1-c9401846ffa0.jpg",
        },
        {
            "content": "급 추워져서 급하게 샀는데 아주 맘에 듭니다 옷 안에 따땃하게 뭐가 있고 디자인도 이쁘고 휘뚜루마뚜루 입 기 좋네용 이 크기에 적당한 무게인것같고 길이가 좀 긴가? 싶었는데 적당한거 같네요",
            "gender": "F",
            "height": "173",
            "weight": "77",
            "product_size": "L",
            "image": "/home/myungjune/projects/maifit-server/temp/741f4d9d-87c8-4808-9d42-70e158dc3e52.jpg",
        },
    ]

    bse = BodyShapeEstimator()
    for review_obj in reviews_obj:
        img_path = review_obj["image"]
        assert os.path.exists(img_path)

        est = bse.extract_betas_and_mesh(img_path)
        if est is not None:
            betas = est["betas"]
            mesh_path = est["meshed_image"]
            print(betas)
            print(mesh_path)
        else:
            print("person not found")
        print()


if __name__ == "__main__":
    main()
