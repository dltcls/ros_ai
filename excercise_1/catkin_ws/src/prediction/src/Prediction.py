#!/usr/bin/env python

import cv2
import numpy as np
import rospy
import tensorflow as tf
from keras import backend as k
from cv_bridge import CvBridge
from keras.models import load_model
from sensor_msgs.msg import CompressedImage
from std_msgs.msg import Bool, Int32
from std_msgs.msg import String
from std_msgs.msg import Float32
from sensor_msgs.msg import Image
from keras import backend as K


class Prediction:
    global_random_predictions = list() 
    
    def __init__(self, subscribe_specific=True, subscribe_random=True):
        self.cv_bridge = CvBridge()
        path_to_model = "/home/ros18/KI/ros_robotics/excercise_1/ai_train/models/weights-best.hdf5" #model weights from training
        
        #Aufgabe 1.4 - Include the model in Prediction.py
        self.model = load_model(path_to_model)
        self.model._make_predict_function() #Initialize before threading
        self.false_predicted_counter = 0
        
        if(subscribe_specific):
        
            ## Tasks "SPECIFIC"            
            #Aufgabe 1.2
            #Subscriber to /camera/output/specific/compressed_img_msgs
            self.start_specific_subscriber()
            
            #Aufgabe 1.5
            #Publisher to '/camera/input/specific/number'
            self.prediction_publisher = rospy.Publisher("/camera/input/specific/number",
                                                            Int32,
                                                            queue_size=1)
            #Aufgabe 1.6
            #Subscriber (Check) to /camera/output/specific/check
            self.start_specific_subscriber_check()
            
        if(subscribe_random):
            ## Tasks "RANDOM"            
            #Aufgabe 2.1
            # Subscriber to /camera/output/random/compressed_img_msgs 
            self.start_random_subscriber_check()
            
            #Aufgabe 2.2
            #Subscriber to /camera/output/random/number - verifiy prediction
            self.start_random_subscriber()
            
          
       
        #Make Keras predict on more threads
        self.session = k.get_session()
        self.graph = tf.get_default_graph()
        self.graph.finalize() #thread-safe
        
        
        self.random_predictions = []

    def process_image(self, image):
        """ Excercise: 21-11-2018 """
        image_expanded = np.expand_dims(image, axis=0) #(1,28,28)
        image_expanded_pred = np.expand_dims(image_expanded,axis=3)
        return image_expanded_pred
        
       
     
    #### Callbacks
    
    ### SPECIFIC
    def callback_img_specific(self, data):
        image = self.cv_bridge.compressed_imgmsg_to_cv2(data) #Retrieves images from data
        image_for_prediction = self.process_image(image) #Convert image, in order to be elaborate
        
        #Prediction - one hot encoded
        prediction_ohe =  self.model.predict(image_for_prediction) 
        
        #Prediction as a real number 
        prediction = np.argmax(prediction_ohe, axis=None, out=None) 
        
        #Publish predicted value through Publisher
        self.prediction_publisher.publish(prediction)
        
        
    def callback_check_specific(self, data):
        rospy.loginfo("Specific number check: The prediction was {}".format(data.data))
       

    ###RANDOM
    
    def callback_img_random(self, data):
        #Process image
        image = self.cv_bridge.compressed_imgmsg_to_cv2(data) #Retrieves images from data
        image_for_prediction = self.process_image(image) #Convert image, in order to be elaborate
        
        #Prediction - one hot encoded
        prediction_ohe =  self.model.predict(image_for_prediction) 
        #Prediction as a real number 
        prediction = np.argmax(prediction_ohe, axis=None, out=None)         
        #List
        Prediction.global_random_predictions.append(prediction)    
        
    
    def callback_check_random(self,data):
        #best prediction match
        rate = rospy.Rate(1)
        rate.sleep()
        
        number = data
        self._verify(number)

    def _verify(self, number, index=-1):
        number = number.data 
        #Debugging 
       # print("Random predictions status: ", Prediction.global_random_predictions)
       # print("Size:", len(Prediction.global_random_predictions))
        
        prediction = Prediction.global_random_predictions[index]
        
        if(number == prediction):
            result = True
        else:
            result = False
            self.false_predicted_counter+=1
        
       
        rospy.loginfo("Actual number is {}, predicted number is {}.\n Prediction was {}".format(number, prediction, result))  
        #Debugging
        if(self.false_predicted_counter>0):
            #It works most of the time
            msg = str(self.false_predicted_counter) + " times the prediction did not work"
            rospy.loginfo(msg)
        
        
    ### Start subscribers
    ### SPECIFIC
    
    def start_specific_subscriber(self):
        rospy.loginfo("Subscribe to specific images")
        specific_topic = '/camera/output/specific/compressed_img_msgs'
        rospy.Subscriber(specific_topic,
                         CompressedImage, 
                         self.callback_img_specific, 
                         queue_size = 1)
        
    
    def start_specific_subscriber_check(self):
        rospy.loginfo("Subscribe to specific check channel")
        topic = "/camera/output/specific/check"
        rospy.Subscriber(topic,
                         Bool, 
                         self.callback_check_specific, 
                         queue_size = 1)
     
    ### RANDOM     
    def start_random_subscriber_check(self):
        rospy.loginfo("Subscribe to random check")
        topic = "/camera/output/random/number"
        rospy.Subscriber(topic,
                         Int32, 
                         self.callback_check_random,
                         queue_size = 1
                         )
       
   
    def start_random_subscriber(self):
        rospy.loginfo("Subscribe to random images")
        topic = "/camera/output/random/compressed_img_msgs"
        rospy.Subscriber(topic,
                         CompressedImage, 
                         self.callback_img_random,
                         queue_size = 1
                         )


def main():
    try:
        # register node
        rospy.init_node('prediction', anonymous=False)

        # init CameraPseudo
        pred = Prediction()

        while not rospy.is_shutdown():
          rospy.spin()

    except rospy.ROSInterruptException:
        pass


if __name__ == '__main__':
    main()
