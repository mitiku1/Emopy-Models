from __future__ import print_function
from models import getMultiInputEmopyModel,getImageInputModel,getDlibFeaturesInputModel
import keras
from dataset import load_dataset_files,load_images_features,generator_face_features,generator_face_images,generator_dlib_features,load_face_images
import os
import numpy as np
np.seterr(divide='ignore', invalid='ignore')
from keras.models import model_from_json

def load_model(json_path,weights_path):
    with open(json_path) as json_file:
        model = model_from_json(json_file.read())
        model.load_weights(weights_path)
        return model

class CustomCallBack(keras.callbacks.Callback):
    def __init__(self,model_name):
        self.model_name = model_name
    def on_epoch_end(self,epoch,logs={}):
        self.model.save_weights("logs/models/last_weights-"+self.model_name+".h5")

def start_training(args):
    """Builds and trains a emopy model
    
    Arguments:
        args {dict} -- dictionary containing model and training parameters
    """
    if args.features=="image":
        model = getImageInputModel(args.input_shape,7)
    elif args.features == "dlib":
        model = getDlibFeaturesInputModel(7)
    else:
        image_model = load_model("logs/models/model-im.json","logs/models/model-im.h5")
        for i in range(len(image_model.layers)):
            image_model.layers[i].name += "-image"
        
        dlib_model = load_model("logs/models/model-dp.json","logs/models/model-dp.h5")
        for i in range(len(dlib_model.layers)):
            dlib_model.layers[i].name += "-dlib"

        model = getMultiInputEmopyModel(image_model,dlib_model,args.input_shape,7)
        
    model.compile(loss=keras.losses.categorical_crossentropy,optimizer=keras.optimizers.Adam(args.lr),metrics=["accuracy"])
    model.summary()
    train_model(model,args)

def train_image_input_model(model,args):
    
    train,test = load_dataset_files(args.dataset_dir)
    test_dataset_folder = os.path.join(args.dataset_dir,"test")
    test_images,test_labels = load_face_images(test_dataset_folder,test[0],test[1],args.input_shape)

    test_images = test_images.astype(np.float32)/255
    
    x_test = test_images
    y_test = np.eye(7)[test_labels]

    model.fit_generator(generator_face_images(args.dataset_dir,train[0],train[1],args),callbacks=[CustomCallBack("image")],epochs=args.epoch,steps_per_epoch = args.step,verbose=1,validation_data=[x_test,y_test])
    model.save_weights("logs/models/model-im.h5")
    score = model.evaluate(x_test, y_test)
    model_json = model.to_json()
    with open("logs/models/model-im.json","w+") as j_file:
        j_file.write(model_json)

    with open("logs/logs/log-im.txt","a+") as log_file:
        log_file.write("Score:"+str(score)+"\n")
def train_dlib_features_input_model(model,args):
    train,test = load_dataset_files(args.dataset_dir)
    test_dataset_folder = os.path.join(args.dataset_dir,"test")
    _,test_dlib_points,test_dlib_points_distances,test_dlib_points_angles,test_labels = load_images_features(test_dataset_folder,test[0],test[1],args.input_shape)

    IMAGE_HEIGHT = args.input_shape[0]
    test_dlib_points = test_dlib_points.astype(np.float32)/IMAGE_HEIGHT
    test_dlib_points_distances = test_dlib_points_distances.astype(np.float32)/IMAGE_HEIGHT
    test_dlib_points_angles = test_dlib_points_angles.astype(np.float32)/np.pi

    x_test = [test_dlib_points,test_dlib_points_distances,test_dlib_points_angles]
    y_test = np.eye(7)[test_labels]

    model.fit_generator(generator_dlib_features(args.dataset_dir,train[0],train[1],args),callbacks=[CustomCallBack("dlib")],epochs=args.epoch,steps_per_epoch = args.step,verbose=1,validation_data=[x_test,y_test])
    model.save_weights("logs/models/model-dp.h5")

    model_json = model.to_json()
    with open("logs/models/model-dp.json","w+") as j_file:
        j_file.write(model_json)
    score = model.evaluate(x_test, y_test)
    with open("logs/logs/log-dp.txt","a+") as log_file:
        log_file.write("Score:"+str(score)+"\n")
def train_face_features_input_model(model,args):
    train,test = load_dataset_files(args.dataset_dir)
    test_dataset_folder = os.path.join(args.dataset_dir,"test")
    test_images,test_dlib_points,test_dlib_points_distances,test_dlib_points_angles,test_labels = load_images_features(test_dataset_folder,test[0],test[1],args.input_shape)

    test_images = test_images.astype(np.float32)/255
    IMAGE_HEIGHT = args.input_shape[0]
    test_dlib_points = test_dlib_points.astype(np.float32)/IMAGE_HEIGHT
    test_dlib_points_distances = test_dlib_points_distances.astype(np.float32)/IMAGE_HEIGHT
    test_dlib_points_angles = test_dlib_points_angles.astype(np.float32)/np.pi

    x_test = [test_images,test_dlib_points,test_dlib_points_distances,test_dlib_points_angles]
    y_test = np.eye(7)[test_labels]

    model.fit_generator(generator_face_features(args.dataset_dir,train[0],train[1],args),callbacks=[CustomCallBack("all")],epochs=args.epoch,steps_per_epoch = args.step,verbose=1,validation_data=[x_test,y_test])
    model.save_weights("logs/models/model-ff.h5")

    model_json = model.to_json()
    with open("logs/models/model-ff.json","w+") as j_file:
        j_file.write(model_json)
    score = model.evaluate(x_test, y_test)
    with open("logs/logs/log-ff.txt","a+") as log_file:
        log_file.write("Score:"+str(score)+"\n")

def train_model(model,args):
    if args.features == "image":
        if os.path.exists("logs/models/last_weights-image.h5"):
            print ("loading saved model")
            model.load_weights("logs/models/last_weights-image.h5")
       
        train_image_input_model(model,args)
    elif args.features == "dlib":
        if os.path.exists("logs/models/last_weights-dlib.h5"):
            print ("loading saved model")
            model.load_weights("logs/models/last_weights-dlib.h5")
      
        train_dlib_features_input_model(model,args)
    else:
        if os.path.exists("logs/models/last_weights-all.h5"):
            print ("loading saved model")
            model.load_weights("logs/models/last_weights-all.h5")
       
        train_face_features_input_model(model,args)
    
    
