# Copyright 2020 The FedLearner Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# coding: utf-8

import unittest
import logging
import threading
import time
from fedlearner.trainer import bridge
import tensorflow.compat.v1 as tf

from fedlearner.trainer.bridge import Bridge
from fedlearner.common import trainer_worker_service_pb2 as tws_pb

def fake_start_message(seq_num, iter_id):
    return tws_pb.TrainerWorkerMessage(
        seq_num=seq_num,
        start=tws_pb.StartMessage(iter_id=iter_id)
    )


class TestBridge(unittest.TestCase):
    def test_bridge(self):
        bridge1 = Bridge('leader', 49951, 'localhost:49952')
        bridge2 = Bridge('follower', 49952, 'localhost:49951')

        t = threading.Thread(target=lambda _: bridge1.connect(), args=(None,))
        t.start()
        bridge2.connect()
        t.join()

        g1 = tf.Graph()
        with g1.as_default():
            x = tf.constant(3.0, name='x')
            y = tf.constant(2.0, name='y')
            send_x = bridge1.send_op('x', x)
            send_y = bridge1.send_op('y', y)

        g2 = tf.Graph()
        with g2.as_default():
            recv_x = bridge2.receive_op('x', dtype=tf.float32)
            recv_y = bridge2.receive_op('y', dtype=tf.float32)
            out = recv_x - recv_y

        bridge1.start()
        bridge2.start()
        with tf.Session(graph=g1) as sess:
            sess.run([send_x, send_y])
        with tf.Session(graph=g2) as sess:
            self.assertEqual(sess.run(out), 1.0)
        bridge1.commit()
        bridge2.commit()

        time.sleep(3)

        t = threading.Thread(target=lambda _: bridge1.terminate(), args=(None,))
        t.start()
        bridge2.terminate()
        t.join()

if __name__ == '__main__':
        logging.basicConfig(level=logging.DEBUG)
        unittest.main()
