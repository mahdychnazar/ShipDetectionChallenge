import tensorflow as tf
import metrics as mt
import utils as ut

#print(tf.config.list_physical_devices('GPU'))
print(f'Tensorflow version {tf.__version__}')
print(tf.config.list_physical_devices("GPU"))

#The model does not  reproduce the original U-net architecture, but it implements the general concept of it.

#Input layer of appropriate size
def input_layer():
    return tf.keras.layers.Input(shape=(768, 768) + (3,))

#Downsamples an image
def encoder_block(filters, size, batch_norm=True):
    #initialize model weights with all zeroes
    initializer = tf.keras.initializers.GlorotNormal()
    #The result layer is a sequence of layers applied one-by-one
    result = tf.keras.Sequential()

    #Convolution layer
    result.add(
        tf.keras.layers.Conv2D(filters, size, padding='same',
                               kernel_initializer=initializer, use_bias=False))

    #Max-pooling the output
    result.add(
        tf.keras.layers.MaxPool2D((2,2), padding = 'same')
    )

    #Batch-normalization for better generalization
    if batch_norm:
        result.add(tf.keras.layers.BatchNormalization())

    #Applying rectified linear unit to the output of the convolution
    result.add(tf.keras.layers.LeakyReLU())

    return result

#Upsamples an image back after downsampling is complete.
#According to U-net concept each upsample block takes the output of corresponding downsample block as input
def decoder_block(filters, size, dropout=False):
    initializer = tf.keras.initializers.GlorotNormal()
    # The result layer is a sequence of layers applied one-by-one
    result = tf.keras.Sequential()

    #Transpose convolution layer reverses the convolution
    result.add(
        tf.keras.layers.Conv2DTranspose(filters, size, strides=2, padding='same',
                                        kernel_initializer=initializer, use_bias=False))

    #Dropout to prevent overfitting
    if dropout:
        result.add(tf.keras.layers.Dropout(0.25))

    #Batch-normalization for better generalization
    result.add(tf.keras.layers.BatchNormalization())

    #Applying rectified linear unit to the output of the convolution
    result.add(tf.keras.layers.ReLU())
    return result


#The last layer of upsampling according to U-net concept it takes the output of the inpul layer as an input
def output_layer(size):
    initializer = tf.keras.initializers.GlorotNormal()
    return tf.keras.layers.Conv2DTranspose(1, size, strides=2, padding='same',
                                           kernel_initializer=initializer, activation='sigmoid')

inp_layer = input_layer()

#Stack encoder and decoder blocks together to implement skip-connections
encoder_blocks = [
    encoder_block(4, 3, batch_norm=False),
    encoder_block(8, 3),
    encoder_block(16, 3),
    encoder_block(32, 3),
    encoder_block(64, 3),
    encoder_block(128, 3),
    encoder_block(256, 3),
    encoder_block(256, 3),

]

decoder_blocks = [

    decoder_block(256, 3, dropout=True),
    decoder_block(256, 3, dropout=True),
    decoder_block(128, 3, dropout=True),
    decoder_block(64, 3),
    decoder_block(32, 3),
    decoder_block(16, 3),
    decoder_block(4, 3)

]

out_layer = output_layer(3)

x = inp_layer
#Outputs of encoder blocks are saved to pass them into corresponding decoder blocks as input
skip_cons = []
for block in encoder_blocks:
    x = block(x)
    skip_cons.append(x)
skip_cons = reversed(skip_cons[:-1])

#Concatenating encoder and decoder blocks so that encoder output is passed as decoder input
for up_block, down_block in zip(decoder_blocks, skip_cons):
    x = up_block(x)
    x = tf.keras.layers.Concatenate()([x, down_block])

#Here is my small unet ready
small_unet = tf.keras.Model(inputs=inp_layer, outputs=out_layer(x))

#Save model summary into .txt file
small_unet.summary(print_fn=ut.myprint)

#Setting up optimizer wit h start learning rate
opt = tf.keras.optimizers.Adam(learning_rate=0.01)
#Compiling the model
small_unet.compile(optimizer=opt, loss=[mt.dice_loss], metrics=[mt.dice_score])

model_file = './model/best_small_unet.h5'
log_file = './log/log.csv'

#Callbacks to optimize training
callbacks = [
    #Saves model weights if loss on validation set improves
    tf.keras.callbacks.ModelCheckpoint(model_file, verbose=1, save_best_only=True),
    #Reduces learning rate by 10 times if loss does not improve after 1 epochs of learning
    tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.1, patience=1),
    #Logger
    tf.keras.callbacks.CSVLogger(log_file),
    #Stops training if loss does not improve after 3 epochs of learning
    tf.keras.callbacks.EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=False)
]

def small_unet_train(train_data, val_data, epochs):
    small_unet.fit(train_data,
                   validation_data=val_data,
                   epochs=epochs,
                   initial_epoch=0,
                   callbacks=callbacks
                   )
    small_unet.save_weights('./model/last_small_unet.h5')

img_file = './/modelgraph//model_grapg.png'
tf.keras.utils.plot_model(small_unet, to_file=img_file, show_shapes=True, show_layer_names=True)