from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch

# Model bilgisi
model_name = "MODEL_NAME"
hf_token = "YOUR_TOKEN"  # Buraya kendi HuggingFace token'ını koy

print("Model ve tokenizer yükleniyor, lütfen bekleyin...")

# Tokenizer ve model yükle
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False, token=hf_token)
model = AutoModelForCausalLM.from_pretrained(model_name, token=hf_token, torch_dtype=torch.float16, device_map="auto")

# Pipeline
generator = pipeline("text-generation", model=model, tokenizer=tokenizer)

print("Model yüklendi. Sorunu sorabilirsin!")

# Kullanıcıdan input al ve cevabı temizle
while True:
    user_input = input("Sen: ")
    if user_input.lower() in ["çık", "exit", "quit", "çıkış"]:
        print("Görüşürüz!")
        break

    # Prompt formatı Vicuna için tipik olarak şöyle olabilir:
    prompt = f"USER: {user_input}\nASSISTANT:"
    
    outputs = generator(
        prompt,
        max_length=512,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        top_k=50,
        num_return_sequences=1,
        pad_token_id=tokenizer.eos_token_id
    )

    # Üretilen metni temizle
    generated_text = outputs[0]["generated_text"]

    # Prompt'tan sonrasını ayıkla
    answer = generated_text.split("ASSISTANT:")[-1].strip()

    print("Bot:", answer)


