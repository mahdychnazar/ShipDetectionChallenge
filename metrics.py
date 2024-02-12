import tensorflow as tf

#Calculating dice coefficient
def dice_score(y_true, y_pred):
    y_t_f = tf.reshape(y_true, [-1])
    y_p_f = tf.reshape(y_pred, [-1])
    y_t_f = tf.cast(y_t_f, tf.float32)
    y_p_f = tf.cast(y_p_f, tf.float32)

    #Dice = 2(A*B)/A+B
    intersection = tf.reduce_sum(y_t_f * y_p_f)
    union = tf.reduce_sum(y_t_f) + tf.reduce_sum(y_p_f)

    dice = (2. * intersection) / union

    return dice

#Loss function to be minimized
def dice_loss(a, b):
    return 1 - dice_score(a, b)
