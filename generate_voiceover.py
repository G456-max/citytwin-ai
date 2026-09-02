import win32com.client
from pathlib import Path

OUTPUT_WAV = "citytwin_ai_voiceover.wav"

narration_script = """
Welcome to CityTwin AI. In the historic city of Rajamahendravaram, Andhra Pradesh, municipal engineers face a critical challenge along the Godavari River highway corridor. 

To widen the highway to four lanes, the city must identify illegal property encroachments, align engineering blueprints with satellite GPS, and quantify roadside tree canopy clearing for environmental approvals. 

Traditional on-ground surveys take weeks and spark legal disputes, while standard generative AI tools hallucinate fake roads. 

CityTwin AI solves this through a dual-engine architecture. 

First, our Three-Point Ground Control Point Snapping solver uses affine matrix math to automatically lock unreferenced CAD blueprints onto real-world WGS84 GPS benchmarks.

Second, in Step One, the deterministic math engine reprojects drone orthomosaics into localized metric UTM Zone 44N coordinates. It performs exact polygon intersection math, identifying structural encroachments down to the centimeter, calculating total square meter overlap and maximum penetration depth with zero hallucinations. Simultaneously, computer vision HSV vegetation filters isolate tree crowns and calculate exact forestry canopy loss.

Third, in Step Two, our Blueprint-Locked Generative Engine uses ControlNet depth conditioning tied directly to the elevation model. It renders photorealistic highway textures, crisp lane markings, and curbs under daylight, monsoon, or night conditions, strictly locked to the engineered geometry.

Finally, in Step Three, CityTwin AI generates a formal municipal compliance audit PDF certificate, complete with itemized discrepancy logs, scorecards, and digital approval seals in a single click.

CityTwin AI: Transforming municipal infrastructure verification with mathematically grounded spatial intelligence.
"""

def generate_voice():
    print(f"Synthesizing voiceover audio to {OUTPUT_WAV}...")
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    stream = win32com.client.Dispatch("SAPI.SpFileStream")
    
    # Set speech rate (-10 to 10, 0 is normal, -1 is slightly slower and clearer)
    speaker.Rate = -1
    speaker.Volume = 100
    
    stream.Open(OUTPUT_WAV, 3, False)
    speaker.AudioOutputStream = stream
    speaker.Speak(narration_script)
    stream.Close()
    print(f"SUCCESS: Voiceover audio saved to {OUTPUT_WAV}!")

if __name__ == "__main__":
    generate_voice()
