import numpy as np
import tensorflow as tf
import os.path

class ImageClassifier:
    def __init__(self, modelPath,labelsPath):
        self.modelPath = modelPath
        self.labelPath = labelsPath
        self.sess = self.create_graph()

    def create_graph(self):
        """Creates a graph from saved GraphDef file and returns a saver."""
        # Creates graph from saved graph_def.pb.
        with tf.gfile.FastGFile(self.modelPath, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            _ = tf.import_graph_def(graph_def, name='')
            return tf.Session()


    def classifyImage(self,image_data, topPrediction):
        # modelFullPath = args["output_graph"]



        softmax_tensor = self.sess.graph.get_tensor_by_name('final_result:0')
        predictions = self.sess.run(softmax_tensor,
                                   {'DecodeJpeg:0': image_data})
        predictions = np.squeeze(predictions)

        top_k = predictions.argsort()[-topPrediction:][::-1]  # Getting top 5 predictions
        f = open(self.labelPath, 'rb')
        lines = f.readlines()

        labels = [str(w).replace("\\n", "").replace("b'", "") for w in lines]
        # labels = [str(w).replace("b'", "") for w in lines]
        print("#######################################################")

        combinedanswer = ''

        for node_id in top_k:
            human_string = labels[node_id]
            score = predictions[node_id]
            combinedanswer = combinedanswer + '%s (Predication = %.2f )' % (human_string, score * 100) + '\n'
            # print('%s (score = %.5f)' % (human_string, score*100))

        answer1 = labels[top_k[0]]
        topscore = predictions[top_k[0]] * 100

        answer = '%s (Predication = %.2f )' % (answer1, topscore)


        return answer1.replace("\'","").strip(),topscore