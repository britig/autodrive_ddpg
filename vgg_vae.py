'''
Created Date: Sunday November 11th 2018
Last Modified: Sunday November 11th 2018 1:13:05 pm
Author: ankurrc
'''
import tensorflow as tf

INPUT_DIMS = (160, 120, 3)
LATENT_DIMS = 1024


def build_encoder():

    input = tf.keras.Input(shape=INPUT_DIMS, name="encoder_input")
    x = tf.keras.layers.ZeroPadding2D(
        padding=(0, 4), name="padded_input")(input)

    filters = 32
    for i in range(1, 3):
        for j in range(1, 3):
            x = tf.keras.layers.Conv2D(
                filters=filters, kernel_size=(3, 3), padding="same", activation="relu", name="block{}_conv{}".format(i, j))(x)
        x = tf.keras.layers.MaxPool2D(
            pool_size=(2, 2), strides=(2, 2), name="block{}_pool".format(i))(x)
        filters *= 2

    for i in range(3, 6):
        for j in range(1, 4):
            x = tf.keras.layers.Conv2D(
                filters=filters, kernel_size=(3, 3), padding="same", activation="relu", name="block{}_conv{}".format(i, j))(x)
        x = tf.keras.layers.MaxPool2D(
            pool_size=(2, 2), strides=(2, 2), name="block{}_pool".format(i))(x)
        filters *= 2

    interim_dims = x.shape[1:]

    # fc
    x = tf.keras.layers.Flatten()(x)

    # output
    z_mean = tf.keras.layers.Dense(
        LATENT_DIMS, activation="relu", name="z_mean")(x)
    z_logvar = tf.keras.layers.Dense(
        LATENT_DIMS, activation="relu", name="z_logvar")(x)

    return tf.keras.Model(inputs=input, outputs=[z_mean, z_logvar], name="encoder"), interim_dims


def build_decoder(interim_dims):

    input = tf.keras.layers.Input(shape=(LATENT_DIMS,), name="decoder_input")
    flattened_interim_dims = interim_dims[0]*interim_dims[1]*interim_dims[2]

    # fc
    x = tf.keras.layers.Dense(flattened_interim_dims,
                              activation="relu", name="fc2")(input)

    x = tf.keras.layers.Reshape(interim_dims)(x)

    filters = 512
    for i in range(1, 4):
        x = UpSampling2D_NN(stride=2, name="block{}_upsample".format(i))(x)
        for j in range(1, 4):
            x = tf.keras.layers.Conv2D(
                filters=filters, kernel_size=(3, 3), padding="same", activation="relu", name="block{}_conv{}".format(i, j))(x)
        filters //= 2

    for i in range(4, 6):
        x = UpSampling2D_NN(stride=2, name="block{}_upsample".format(i))(x)
        for j in range(1, 3):
            x = tf.keras.layers.Conv2D(
                filters=filters, kernel_size=(3, 3), padding="same", activation="relu", name="block{}_conv{}".format(i, j))(x)
        filters //= 2

    x = tf.keras.layers.Conv2D(filters=3, kernel_size=(
        3, 3), activation="relu", padding="same", name="padded_output")(x)
    output = tf.keras.layers.Cropping2D(cropping=(0, 4), name="output")(x)

    return tf.keras.Model(inputs=input, outputs=output, name="decoder")


def sample(self, z_mean, z_logvar):

    batch = tf.shape(z_mean)[0]
    dims = tf.shape(z_mean)[1]
    epsilon = tf.random_normal(shape=(batch, dims))

    return z_mean + tf.exp(z_logvar)*epsilon


def main():
    encoder, dim = build_encoder()

    decoder = build_decoder(dim)

    encoder.summary()
    decoder.summary()


if __name__ == "__main__":
    main()
