import gym
import numpy as np
import pickle,os
import matplotlib.pyplot as plt
import math
import Box2D
import tensorflow as tf

os.system('clear')
print('LunarLander Deep Learning')

env = gym.make('LunarLander-v2')

# env = gym.wrappers.Monitor(env, directory, video_callable=lambda episode_id: True)


# print(env.action_space)
# print(env.observation_space)
# print(env.observation_space.high)
# print(env.observation_space.low)

def one_hot(x,ab):
    return np.array(np.arange(ab) == x,dtype=np.int32)

def reform_rewards(R_list):
    batch_RDecayed = list(R_list)
    cumulative = 0
    for r in reversed(range(len(batch_R))):
        cumulative = cumulative * reward_decay + batch_R[r]
        batch_RDecayed[r] = cumulative
    # normalize
    batch_RDecayed -= np.mean(batch_RDecayed)
    batch_RDecayed /= np.std(batch_RDecayed)
    return batch_RDecayed
'''
TF ::
'''

NUM_INPUTS  = 8
NUM_HIDDEN1 = 10
NUM_HIDDEN2 = 10
NUM_OUTPUT  = 4


# learning_rate= 5e-4
reward_decay=0.96
epsilon = 0.02

for learning_rate in [1e-3,1e-2,1e-1]:
    graph = tf.Graph()

    with graph.as_default():
            # Inputs:
            with tf.name_scope('Inputs'):
                tf_X = tf.placeholder(tf.float32,shape=(None,NUM_INPUTS)) # 3: (state,action,reward)
                tf_Y = tf.placeholder(tf.int32,shape=(None,NUM_OUTPUT)) # 4:(left,right,bottom,none) 'boosters'
                tf_discounted_reward_normd = tf.placeholder(tf.float32,shape=(None)) # depends on length of episode
                dropout = tf.placeholder_with_default(1.0, shape=())
                cost = tf.placeholder(tf.float32,shape=())

            # Varaibles
            with tf.name_scope('Variables'):


                W1 = tf.Variable(tf.random_normal([NUM_INPUTS,NUM_HIDDEN1],stddev=0.3))
                B1 = tf.Variable(tf.constant(0.1,shape=[NUM_HIDDEN1]))

                W2 = tf.Variable(tf.random_normal([NUM_HIDDEN1,NUM_HIDDEN2],stddev=0.3))
                B2 = tf.Variable(tf.constant(0.1,shape=[NUM_HIDDEN2]))

                W3 = tf.Variable(tf.random_normal([NUM_HIDDEN2,NUM_OUTPUT],stddev=0.3))
                B3 = tf.Variable(tf.constant(0.1,shape=[NUM_OUTPUT]))


            # Dimension check

            print('tf_X: ',tf_X.shape)
            print('tf_Y: ',tf_Y.shape)
            print('tf_discounted_reward_normd: ',tf_discounted_reward_normd.shape)

            print('W1: ',W1.shape)
            print('B1: ',B1.shape)
            print('W2: ',W2.shape)
            print('B2: ',B2.shape)
            print('W3: ',W3.shape)
            print('B3: ',B3.shape)


            # Feed Forward
            with tf.name_scope('FeedForward'):
                A1 = tf.matmul(tf_X,tf.nn.dropout(W1,dropout)) + B1
                Relu = tf.nn.relu(A1)
                A2 = tf.matmul(Relu,tf.nn.dropout(W2,dropout)) + B2
                Relu = tf.nn.relu(A2)
                A3 = tf.matmul(Relu,W3) + B3

            a_prob = tf.nn.softmax(A3)

            with tf.name_scope('Training'):
                softmax_x_entropy = tf.nn.softmax_cross_entropy_with_logits(labels = tf_Y,logits=A3)

                loss = tf.reduce_mean(softmax_x_entropy*tf_discounted_reward_normd)# + 0.001*tf.nn.l2_loss(W1) + 0.001*tf.nn.l2_loss(W2) + 0.001*tf.nn.l2_loss(W3)

                optimizer = tf.train.AdamOptimizer(learning_rate).minimize(loss)

            tf.summary.scalar('Score',cost)
            # tf.summary.histogram('Activations',a_prob)

            merged = tf.summary.merge_all()

    with tf.Session(graph=graph) as session:



        tf.global_variables_initializer().run()
        writer = tf.summary.FileWriter('./summary/Alpha'+str(learning_rate),session.graph)
        scores = []

        for episode in range(4000):
            print('========')

            batch_X = []
            batch_Y = []
            batch_R = []

            observation = env.reset()
            state0, reward, done, _ = env.step(env.action_space.sample())
            rtn = 0
            t = -1
            while(True):
                t += 1
            # for t in range(500):
                if episode%1000 == 0:
                    env.render()

                if (np.random.random() < epsilon):
                    action = env.action_space.sample()
                else:
                    action_prob = session.run([a_prob],feed_dict = {tf_X:[state0],dropout:1.})[0][0]
                    action = np.random.choice(range(NUM_OUTPUT), p = action_prob) # biased sampling of actions, returns 0,1,2,3

                state, reward, done, _ = env.step(action)
                rtn += reward

                # save frame to memory
                batch_X.append(state0)
                batch_Y.append(one_hot(action,NUM_OUTPUT))
                batch_R.append(reward)

                state0 = state

                if done or (t >= 500):
                        print("Episode [{}] finished after [{}] timesteps reward [{}] Avg Score100 [{}]".format(episode+1,t,rtn,np.mean(scores[-100:])))
                        scores.append(rtn)
                        break

            # TensorBoard




            # Initialize episode rewards
            batch_RD = reform_rewards(batch_R)

            # Train network after episode
            print('Training Network')
            feed_dict = {tf_X:batch_X,tf_Y:batch_Y,tf_discounted_reward_normd:batch_RD,dropout:0.98,cost:rtn}
            _ ,summary = session.run([optimizer,merged],feed_dict=feed_dict)
            print('Trained..')

            writer.add_summary(summary,episode)




print('DONE !!!')
