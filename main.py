import requests
import json

# LM Studio'da çalışan sunucunun adresi
# Eğer LM Studio'da farklı bir port kullanıyorsan, burayı değiştirmelisin.
API_URL = "Your_local_host_port" # Doğru API endpoint'i

def get_response_from_lm_studio(prompt):
    """
    LM Studio'daki yapay zeka modeline mesaj gönderir ve yanıtı alır.
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 1000 
    }

    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(data))
        response.raise_for_status() # HTTP hatalarını kontrol et
        
        response_data = response.json()
        
        if 'choices' in response_data and len(response_data['choices']) > 0:
            model_response = response_data['choices'][0]['message']['content']
            return model_response
        else:
            print("Hata: LM Studio'dan geçerli bir yanıt alınamadı. Yanıt formatı beklenenden farklı.")
            print(f"Dönen yanıt: {response_data}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"İstek sırasında bir hata oluştu: {e}")
        return None
    except json.JSONDecodeError:
        print("Hata: LM Studio'dan gelen yanıt geçerli bir JSON formatında değil.")
        return None

def main():
    """
    Kullanıcının terminalden yazmasını ve modelle konuşmasını sağlar.
    """
    print("LM Studio ile sohbet etmeye hazırız. Çıkmak için 'çık' yazın.")
    
    while True:
        user_input = input("Sen: ")
        
        if user_input.lower() == 'çık':
            print("Görüşmek üzere!")
            break
            
        response = get_response_from_lm_studio(user_input)
        
        if response:
            print(f"Model: {response}")

if __name__ == "__main__":
    main()
