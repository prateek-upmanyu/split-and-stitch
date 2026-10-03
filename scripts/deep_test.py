import asyncio
from pathlib import Path
import random
from app.main import generate_hf_wan_animate, generate_hf_echomimic, generate_hf_sadtalker

async def test_all():
    scratch = Path("C:/Users/khadk/.gemini/antigravity/brain/00657df0-ef7d-495e-9f66-d4831ce860dc/scratch")
    char = scratch / "test_character.png"
    vid = scratch / "test_5s.mp4"
    audio = scratch / "dummy_audio.mp3"
    
    print("=== DEEP TEST INITIATED ===")
    
    print("\n1. Testing EchoMimic (ZeroGPU)...")
    try:
        # Note: testing full EchoMimic generation might take ~60s
        print("Uploading & Generating...")
        res = await generate_hf_echomimic(char, audio)
        print("Success! Output:", res)
    except Exception as e:
        print("EchoMimic Failed:", e)

    print("\n2. Testing Wan2.2 (ZeroGPU)...")
    try:
        # Pass small valid duration
        res = await generate_hf_wan_animate(vid, char, max_duration=2, resolution="Low Res")
        print("Success! Output:", res)
    except Exception as e:
        print("Wan2.2 Failed:", e)
        
    print("\n=== DEEP TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(test_all())

