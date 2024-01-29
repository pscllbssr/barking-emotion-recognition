import keras
import pandas as pd
import numpy as np
from keras.src.applications import ResNet50
from keras.src.metrics import F1Score
from matplotlib import pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report, ConfusionMatrixDisplay
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense
from keras.utils import to_categorical
from audio_preprocessing import generate_spectrogram, random_frequency_mask
import seaborn as sns
from sklearn.utils.class_weight import compute_class_weight

# read dataset
df = pd.read_csv('data/dataset.csv')

# choose what to include in the model
df = df[df.label.isin(['Playfulness', 'Aggressiveness', 'Happiness', 'Despair'])]

# Apply feature extraction to each audio file
df['spectrogram'] = df.apply(lambda row: generate_spectrogram(f"data/audioset_audios/{row['ytid']}_{int(row['start'])}_{int(row['stop'])}_cut.mp3"), axis=1)

# show files not found
print(f"{df['spectrogram'].isna().sum()} entries dropped because no audio file found.")

# Remove rows where spectrogram is None (i.e., file not found)
df = df.dropna(subset=['spectrogram'])

# Encode emotion labels
label_encoder = LabelEncoder()
df['emotion_label_encoded'] = label_encoder.fit_transform(df['label'])

# Create X (features) and y (labels)
data = np.array(df['spectrogram'].tolist())
labels = to_categorical(df['emotion_label_encoded'])  # One-hot encode labels

# Perform train-test split
X_train, X_test, y_train, y_test = train_test_split(data, labels, test_size=0.2, random_state=42)

# Add a fourth dimension to the input images
X_train = np.expand_dims(X_train, axis=-1)
X_test = np.expand_dims(X_test, axis=-1)

# Define ResNet50 model
resnet_model = Sequential()
resnet_model.add(Conv2D(3, (3, 3), input_shape=X_train.shape[1:]))  # Convert grayscale to RGB
resnet_model.add(ResNet50(include_top=False, pooling='avg', weights='imagenet'))
resnet_model.add(Dense(512, activation='relu'))
resnet_model.add(Dense(labels.shape[1], activation='softmax'))

# Freeze the pre-trained layers
resnet_model.layers[0].trainable = False

# Compile model
resnet_model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])

# Print model summary
resnet_model.summary()

# Train model
resnet_model.fit(X_train, y_train, batch_size=32, epochs=10, validation_data=(X_test, y_test))

# Evaluate model
loss, accuracy = resnet_model.evaluate(X_test, y_test)
print("Test Accuracy:", accuracy)
print("")

# Predictions
y_pred = resnet_model.predict(X_test)

# Convert predictions from one-hot encoding to class labels
y_pred_labels = np.argmax(y_pred, axis=1)
y_true_labels = np.argmax(y_test, axis=1)

# Confusion matrix
conf_matrix = confusion_matrix(y_true_labels, y_pred_labels)
plt.figure(figsize=(10, 7))
sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
            xticklabels=label_encoder.classes_,
            yticklabels=label_encoder.classes_)
plt.xlabel('Predicted')
plt.ylabel('True')
plt.title('Confusion Matrix')
plt.show()

# Classification report
class_report = classification_report(y_true_labels, y_pred_labels)
print("Classification Report:")
print(class_report)

# model export
resnet_model.save('models/model_resnet50.keras')