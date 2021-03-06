import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
import math
from datetime import datetime

# Helper code for plotting and reading Burgers' input files
def read_me(*args):
    return np.hstack([np.loadtxt(x) for x in args])

def plot_it(v, i, v_indices = np.array([0]), pltaxis = None):
    fig = plt.figure(figsize=(6,6)) #12,6
    if np.sum(v_indices) == 0:
         vspace = np.linspace(0.0, 100.0, 1000)[:, None]
         plt.plot(vspace, v, lw=2)
    else:
         vspace = v_indices
         plt.plot(vspace, v, 'ro')
    if pltaxis != None:
         plt.axis(pltaxis)
    my_path = 'C:\\Users\\Tina\\Desktop\\FRG\\NNs\\Project\\figs\\'
    plt.savefig(my_path + datetime.now().strftime('%H.%M') + '_' + str(i) + '_test.png')  
    #plt.show()

# Code here for importing data from file
snaps =  read_me('burg/snaps_0p02_0p02_5.dat')
input = snaps.T
#plot_it(np.hstack((snaps[:, [150]], snaps[:, [50]])),1)

# Make inputs noisy
#noisy_input = input + .2 * np.random.random_sample((input.shape)) - .1
noisy_input = input
output = input
# Scale to [0,1]
scaled_input_1 = np.divide((noisy_input-noisy_input.min()), (noisy_input.max()-noisy_input.min()))
scaled_output_1 = np.divide((output-output.min()), (output.max()-output.min()))
# Scale to [-1,1]
scaled_input_2 = (scaled_input_1*2)-1
scaled_output_2 = (scaled_output_1*2)-1
input_data = scaled_input_2
output_data = scaled_output_2

#input_data = input
#output_data = output

# Build autoencoder with 3 hidden layers
n_samp, n_input = input_data.shape 
n_hidden = [50,10]
x = tf.placeholder("float", [None, n_input])
# Weights and biases from input to hidden layer 1
Wh1 = tf.Variable(tf.random_uniform((n_input, n_hidden[0]), -1.0 / math.sqrt(n_input), 1.0 / math.sqrt(n_input)))
bh1 = tf.Variable(tf.zeros([n_hidden[0]]))
h1 = tf.nn.tanh(tf.matmul(x,Wh1) + bh1)
# Weights and biases from hidden layer 1 to hidden layer 2 (encoded inputs, mean)
Wh2 = tf.Variable(tf.random_uniform((n_hidden[0], n_hidden[1]), -1.0 / math.sqrt(n_input), 1.0 / math.sqrt(n_input)))
bh2 = tf.Variable(tf.zeros([n_hidden[1]]))
z_mean = tf.nn.tanh(tf.matmul(h1,Wh2) + bh2) #remove tanh if variational
# Weights and biases from hidden layer 1 to hidden layer 2 (encoded inputs, stddev)
Wh2_stddev = tf.Variable(tf.random_uniform((n_hidden[0], n_hidden[1]), -1.0 / math.sqrt(n_input), 1.0 / math.sqrt(n_input)))
bh2_stddev = tf.Variable(tf.zeros([n_hidden[1]]))
z_stddev = tf.sqrt(tf.exp(tf.matmul(h1,Wh2_stddev) + bh2_stddev))
# Variational Autoencoder Samples
#z_mean = h2
#z_stddev = h2_stddev
samples = tf.random_normal([tf.shape(x)[0], n_hidden[1]],0,1,dtype=tf.float32)  
sampled_z = z_mean + (z_stddev * samples) 
# Weights and biases from hidden layer 2 to hidden layer 3
Wh3 = tf.Variable(tf.random_uniform((n_hidden[1], n_hidden[0]), -1.0 / math.sqrt(n_input), 1.0 / math.sqrt(n_input)))
bh3 = tf.Variable(tf.zeros([n_hidden[0]]))
h3 = tf.nn.tanh(tf.matmul(z_mean,Wh3) + bh3) # change to sampled_z if variational
# Weights and biases from hidden layer 2 to output
#Wo = tf.transpose(Wh) # tied weights
Wo = tf.Variable(tf.random_uniform((n_hidden[0], n_input), -1.0 / math.sqrt(n_input), 1.0 / math.sqrt(n_input)))
bo = tf.Variable(tf.zeros([n_input]))
y = tf.nn.tanh(tf.matmul(h3,Wo) + bo)
# Objective functions
y_ = tf.placeholder("float", [None,n_input])
meansq = tf.reduce_sum(tf.square(y_-y))
generation_loss = meansq
# Latent loss from variational autoencoder
latent_loss = 0.5 * tf.reduce_sum(tf.square(z_mean) + tf.square(z_stddev) - tf.log(tf.square(z_stddev)) - 1) 
#loss = tf.reduce_mean(generation_loss + latent_loss) #turn on if variational, turn off next line
loss = tf.reduce_mean(generation_loss)
train_step = tf.train.AdamOptimizer().minimize(loss)

# Run autoencoder
init = tf.initialize_all_variables()
sess = tf.Session()
sess.run(init)
n_rounds = 80000
batch_size = min(125, n_samp)
for i in range(n_rounds):
    sample = np.random.randint(n_samp, size=batch_size)
    batch_xs = input_data[sample][:]
    batch_ys = output_data[sample][:]
    sess.run(train_step, feed_dict={x: batch_xs, y_:batch_ys})
    if i % 100 == 0:
        #print(batch_xs.shape)
        print(i, sess.run(meansq, feed_dict={x: batch_xs, y_:batch_ys})/batch_size)

print("Target:")
print(output_data)
print("Final activations:")
print(sess.run(y, feed_dict={x: input_data}))
print("Final weights (input => hidden layer)")
print(sess.run(Wh3))
print("Final biases (input => hidden layer)")
print(sess.run(bh3))
print("Final biases (hidden layer => output)")
print(sess.run(bo))
print("Final activations of hidden layer")
print(sess.run(h3, feed_dict={x: input_data}))

for i in range(40):
    x1 = sess.run(y, feed_dict={x: input_data})[[i*12],:]
    x2 = input_data[[i*12],:]
    #print(x1.shape)
    #print(x2.shape)
    plot_it(np.hstack((x2.T,x1.T)),i*12)
