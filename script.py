import azure.cognitiveservices.speech as speechsdk
import time
import json
import random
from tqdm import tqdm

# Set up Azure Speech Service configuration
speech_key = "4fb9d1c00ef9415c8e7f1501b1351697"
service_region = "eastus"
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

# Initialize Speech Recognizer
language = 'en-US'
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, language=language, audio_config=audio_config)

# Pronunciation assessment configuration
topics = [
    "Describe your favorite hobby and why you enjoy it.",
    "Explain the process of cooking your favorite meal.",
    "Talk about a memorable trip you have taken.",
    "Discuss the benefits of regular exercise.",
    "Describe your favorite book or movie and why you like it.",
    "Explain a project or task you recently completed at school or work.",
    "Talk about the importance of time management.",
    "Discuss your favorite holiday and how you celebrate it.",
    "Describe a challenge you faced and how you overcame it.",
    "Explain the impact of technology on our daily lives."
]

topic = random.choice(topics)  # Use random.choice for a single topic
print(f"Selected topic: {topic}")
print(topic)
time.sleep(.10)

# Pronunciation assessment configuration
pronunciation_config = speechsdk.PronunciationAssessmentConfig(
    grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
    granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
    enable_miscue=False
)
pronunciation_config.enable_prosody_assessment()
pronunciation_config.enable_content_assessment_with_topic(topic)

# Apply pronunciation configuration to the recognizer
pronunciation_config.apply_to(speech_recognizer)

# Initialize variables for recognition process
done = False
pron_results = []
recognized_text = ""
session_logs = []

# Callbacks for events
def stop_cb(evt):
    """Callback to stop continuous recognition."""
    print(f"CLOSING on {evt}")
    global done
    done = True

def recognized(evt):
    """Callback for handling recognized speech."""
    global pron_results, recognized_text, session_logs
    if evt.result.reason in [speechsdk.ResultReason.RecognizedSpeech, speechsdk.ResultReason.NoMatch]:
        result = speechsdk.PronunciationAssessmentResult(evt.result)
        pron_results.append(result)

        if evt.result.text.strip():
            print(f"Recognizing: {evt.result.text}")
            recognized_text += " " + evt.result.text.strip()
            session_logs.append({
                "text": evt.result.text,
                "accuracy": result.accuracy,
                "fluency": result.fluency,
                "completeness": result.completeness
            })
            print(f"Accuracy: {result.accuracy}, Fluency: {result.fluency}, Completeness: {result.completeness}")

            # Provide real-time feedback based on pronunciation scores
            if result.accuracy < 80:
                print("Feedback: Work on your pronunciation of certain words.")
            elif result.fluency < 80:
                print("Feedback: Try to speak more fluently.")
            elif result.completeness < 80:
                print("Feedback: Complete your sentences more clearly.")
            else:
                print("Great pronunciation!")
filler_words = [
    "um", "uh", "like", "you know", "so", "basically",
    "actually", "I mean", "well", "right", "just", 
    "kind of", "sort of", "anyway", "there you go", 
    "let me think", "er", "hm", "ah", "okay"
]
spoken_text = "Your input speech here"

# Count filler words in the spoken text
filler_word_count = sum(spoken_text.lower().count(word) for word in filler_words)
total_words = len(spoken_text.split())

# Calculate the filler word percentage
filler_word_percentage = (filler_word_count / total_words) * 100 if total_words > 0 else 0

# Provide feedback based on the filler word percentage
if filler_word_percentage > 10:
    print("Feedback: Try to reduce the use of filler words.")
elif filler_word_percentage > 5:
    print("Feedback: Be mindful of using filler words occasionally.")
else:
    print("Good job! You used filler words sparingly.")
# Connect event handlers
speech_recognizer.recognized.connect(recognized)
speech_recognizer.session_started.connect(lambda evt: print(f"SESSION STARTED: {evt}"))
speech_recognizer.session_stopped.connect(lambda evt: print(f"SESSION STOPPED: {evt}"))
speech_recognizer.canceled.connect(lambda evt: print(f"CANCELED: {evt}"))
speech_recognizer.session_stopped.connect(stop_cb)
speech_recognizer.canceled.connect(stop_cb)

# Start continuous recognition
speech_recognizer.start_continuous_recognition()

# Progress bar for timeout display (20 seconds)
timeout = 20  # Duration in seconds
start_time = time.time()
with tqdm(total=timeout, desc="Recognition Progress") as pbar:
    while not done and time.time() - start_time < timeout:
        time.sleep(0.1)
        pbar.update(0.1)

# Stop recognition after the timeout
speech_recognizer.stop_continuous_recognition()
print("Recognition finished.")

# Save session log to a file
if pron_results:
    with open("pronunciation_session_log.json", "w") as f:
        json.dump(session_logs, f, indent=4)
    print("Session log saved to 'pronunciation_session_log.json'.")

# Process content assessment result
if pron_results and pron_results[-1].content_assessment_result is not None:
    content_result = pron_results[-1].content_assessment_result
    print(f"Content Assessment for: {recognized_text.strip()}") 
    print("Content Assessment results:\n"
          f"\tGrammar score: {content_result.grammar_score:.1f}\n"
          f"\tVocabulary score: {content_result.vocabulary_score:.1f}\n"
          f"\tTopic score: {content_result.topic_score:.1f}")
else:
    print("No content assessment results available.")