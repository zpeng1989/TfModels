# From the website: http://www.ctolib.com/topics-101544.html


#1、首先需要安装TensorFlow
# git clone https://github.com/tensorflow/models

#2、其次添加clone的代码库路径，
import os
import sys

#指定TensorFlow使用第一块GPU，否则 tf默认使用所有的内存资源
os.environ["CUDA_VISIBLE_DEVICES"] = '0'
# 指定代码库所在的路径，并将其添加到系统路径中，
sys.path.append("E:\\TfModels\\slim")


from datasets import dataset_utils
import tensorflow as tf

#3、接着下载VGG-16模型，用于图像分类与分割
url = "http://download.tensorflow.org/models/vgg_16_2016_08_28.tar.gz"

#指定保存路径
checkpoints_dir = 'C:\\tmp\\segmentation\\checkpoints'

if not tf.gfile.Exists(checkpoints_dir):
    tf.gfile.MakeDirs(checkpoints_dir)
if not tf.gfile.Exists(os.path.join(checkpoints_dir, 'vgg_16.ckpt')):
	dataset_utils.download_and_uncompress_tarball(url, checkpoints_dir)

# 执行结果如下：
#>>> Downloading vgg_16_2016_08_28.tar.gz 100.0%
#>>> Successfully downloaded vgg_16_2016_08_28.tar.gz 513324920 bytes.



#--------------------------------------------------------------------
# 图像分类
#--------------------------------------------------------------------

from matplotlib import pyplot as plt

import numpy as np
import os, sys
import tensorflow as tf

#urllib和urllib2在python3被统一到rullib中
from urllib.request import urlopen

from datasets import imagenet
from nets import vgg
from preprocessing import vgg_preprocessing

checkpoints_dir = 'C:\\tmp\\segmentation\\checkpoints'

slim = tf.contrib.slim

# 网络模型的输入图像有默认的尺寸； 因此，我们需要先调整输入图片的尺寸
# vgg_16.default_image_size = 224
image_size = vgg.vgg_16.default_image_size

with tf.Graph().as_default():
	url = ("https://upload.wikimedia.org/wikipedia/commons/d/d9/First_Student_IC_school_bus_202076.jpg")

	# 连接网址，下载图片
	image_string = urlopen(url).read()

	# 将图片解码成jpeg格式
	image = tf.image.decode_jpeg(image_string, channels=3)

	# 对图片做缩放操作，保持长宽比例不变，裁剪得到图片中央的区域
	# 裁剪后的图片大小等于网络模型的默认尺寸
	processed_image = vgg_preprocessing.preprocess_image(image, image_size, image_size, is_training=False)

	# 可以批量导入图像； 第一个维度指定每批图片的张数； 我们每次只导入一张图片
	#在指定 axis方向对图像维度进行扩展 [1,Himg,Wimg,Cimg]
	processed_images = tf.expand_dims(processed_image, 0)

	# 创建模型，使用默认的 arg scope参数
	# arg_scope是slim library的一个常用参数,可设置指定网络层的参数，比如stride, padding 等等。
	with slim.arg_scope(vgg.vgg_arg_scope()):
		logits, _ = vgg.vgg_16(processed_images, num_classes=1000, is_training=False)

	# 我们在输出层使用softmax函数，使输出项是概率值
	probabilities = tf.nn.softmax(logits)

	# 创建一个函数，从checkpoint读入网络权值
	init_fn = slim.assign_from_checkpoint_fn(os.path.join(checkpoints_dir, 'vgg_16.ckpt'), slim.get_model_variables('vgg_16'))

	with tf.Session() as sess:

		init_fn(sess) # 加载权值
		
		# 图片经过缩放和裁剪，最终以numpy矩阵的格式传入网络模型
		np_image, network_input, probabilities = sess.run([image, processed_image, probabilities])
		
		probabilities = probabilities[0, 0:]
		sorted_inds = [i[0] for i in sorted(enumerate(-probabilities), key=lambda x:x[1])]

	# 显示下载的图片
	plt.figure()
	plt.imshow(np_image.astype(np.uint8))
	plt.suptitle("Downloaded image", fontsize=14, fontweight='bold')
	plt.axis('off')
	plt.ion()
	plt.show()
	plt.savefig('origin.png')

	# 显示最终传入网络模型的图片, #图像的像素值做[-1, 1]的归一化
	plt.figure()
	plt.imshow( network_input / (network_input.max() - network_input.min()) )
	plt.suptitle("Resized, Cropped and Mean-Centered input to network", fontsize=14, fontweight='bold')
	plt.axis('off')
	plt.ion()
	plt.show()
	plt.savefig('processed.png')


	names = imagenet.create_readable_names_for_imagenet_labels()
	for i in range(5):
		index = sorted_inds[i]
		
		# 打印top5的预测类别和相应的概率值。
		print('Probability %0.2f => [%s]' % (probabilities[index], names[index+1]))

	res = slim.get_model_variables()    



#>>> Probability 1.00 => [school bus]
#>>> Probability 0.00 => [minibus]
#>>> Probability 0.00 => [passenger car, coach, carriage]
#>>> Probability 0.00 => [trolleybus, trolley coach, trackless trolley]
#>>> Probability 0.00 => [cab, hack, taxi, taxicab]







#--------------------------------------------------------------------
# 图像标注与分割
#--------------------------------------------------------------------

# from preprocessing import vgg_preprocessing
# from urllib.request import urlopen

# # 加载像素均值及相关函数
# from preprocessing.vgg_preprocessing import (_mean_image_subtraction, _R_MEAN, _G_MEAN, _B_MEAN)

# # 展现分割结果的函数，以不同的颜色区分各个类别
# def discrete_matshow(data, labels_names=[], title=""):
#     #获取离散化的色彩表
#     cmap = plt.get_cmap('Paired', np.max(data)-np.min(data)+1)
#     mat = plt.matshow(data, cmap=cmap, vmin = np.min(data)-.5, vmax = np.max(data)+.5)
    
#     #在色彩表的整数刻度做记号
#     cax = plt.colorbar(mat, ticks=np.arange(np.min(data),np.max(data)+1))

#     # 添加类别的名称
#     if labels_names:
#         cax.ax.set_yticklabels(labels_names)

#     if title:
#         plt.suptitle(title, fontsize=14, fontweight='bold')


# with tf.Graph().as_default():
#     url = ("https://upload.wikimedia.org/wikipedia/commons/d/d9/First_Student_IC_school_bus_202076.jpg")

#     image_string = urlopen(url).read()
#     image = tf.image.decode_jpeg(image_string, channels=3)

#     # 减去均值之前，将像素值转为32位浮点
#     image_float = tf.to_float(image, name='ToFloat')

#     # 每个像素减去像素的均值
#     processed_image = _mean_image_subtraction(image_float, [_R_MEAN, _G_MEAN, _B_MEAN])

#     #在指定 axis方向对图像维度进行扩展 [1,Himg,Wimg,Cimg]
#     input_image = tf.expand_dims(processed_image, 0)

#     with slim.arg_scope(vgg.vgg_arg_scope()):
#         # spatial_squeeze选项指定是否启用全卷积模式
#         logits, _ = vgg.vgg_16(input_image, num_classes=1000, is_training=False, spatial_squeeze=False)

#     # 得到每个像素点在所有1000个类别下的概率值，挑选出每个像素概率最大的类别
#     # 严格说来，这并不是概率值，因为我们没有调用softmax函数
#     # 但效果等同于softmax输出值最大的类别
#     pred = tf.argmax(logits, dimension=3)

#     init_fn = slim.assign_from_checkpoint_fn( os.path.join(checkpoints_dir, 'vgg_16.ckpt'), slim.get_model_variables('vgg_16') )

#     with tf.Session() as sess:
#         init_fn(sess)
#         segmentation, np_image = sess.run([pred, image])

# # 去除空的维度
# segmentation = np.squeeze(segmentation)

# unique_classes, relabeled_image = np.unique(segmentation, return_inverse=True)

# segmentation_size = segmentation.shape

# relabeled_image = relabeled_image.reshape(segmentation_size)

# labels_names = []

# for index, current_class_number in enumerate(unique_classes):
#     labels_names.append(str(index) + ' ' + names[current_class_number+1])

# discrete_matshow(data=relabeled_image, labels_names=labels_names, title="Segmentation")




##---------------------------------------------------------------------------------------------
## 以上两例都使用VGG-16模型对图像做分类和分割，也可以选用其它占用内存少的网络模型（如AlexNet）进行处理。
## 电脑配置不高的情况下，进了使用耗内存少的模型，这是比较方便验证算法有效性的。
##---------------------------------------------------------------------------------------------





