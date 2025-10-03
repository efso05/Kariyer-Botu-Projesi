import os
import discord
from discord.ext import commands
from google import genai
from google.genai.errors import APIError

# --- TEMEL YAPILANDIRMA ---
# Discord Bot Token'ını ve Gemini API Anahtarını buraya yapıştırın.
DISCORD_TOKEN = "your_token" 
GEMINI_API_KEY = "your_token" 

# --- SOHBET YÖNETİMİ ---
kullanici_sohbetleri = {} # !kariyerbaslat oturumları (Text tabanlı)
uni_sohbetleri = {}      # !universite oturumları (Text tabanlı)
anket_sohbetleri = {}    # !anket oturumları (Buton tabanlı)

# --- ORTAK KULLANILAN UYARI METNİ ---
UYARI_METNI = "Lütfen, bu soruya sadece kariyer analizi ile ilgili mantıklı ve dürüst bir cevap veriniz. Cevabınızı bekliyorum."

# =======================================================================
#                           SYSTEM INSTRUCTION VE SORULAR
# =======================================================================

# --- KARİYER BOTUNUN KİŞİLİĞİ VE GÖREVLERİ (TEXT TABANLI - 3 MESLEK ÖNERİSİ YAPACAK) ---
SYSTEM_INSTRUCTION_KARIYER = (
    "Sen, 12 soruluk bir anket yürüten, tecrübeli ve motive edici bir kariyer danışmanısın. "
    "Davranış Kuralları:\n"
    "1. TÜRKÇE konuş ve daima kibar ol. "
    "2. Kullanıcının cevabı alakasız, garip veya mantıksız ise, aynı soruyu tekrar sor ve kibarca uyarıda bulun. Uyarı metni tam olarak şudur: "
    f"   '{UYARI_METNI}'\n"
    "3. Kullanıcı mantıklı cevap verdiğinde, cevabı onaylayan kısa bir geri bildirim ver (bir sonraki soruyu botun kendisi sorsun). "
    "4. 12. soruya cevap alındığında, tüm sohbet geçmişini analiz ederek EN AZ 3 meslek önerisi yap ve her birini gerekçeleriyle açıkla. **Her öneriyi, GEREKÇELERİ dahil 3-4 cümleyle özetle ve kesinlikle 1500 karakteri aşma.** "
    "5. 12. sorunun ardından analiz yap, başka soru sorma."
    "6. **ANALİZ VE ÖNERİLER BİTTİKTEN SONRA, KESİNLİKLE EK BİR KAPANIŞ CÜMLESİ VEYA TEŞEKKÜR YAZMA. Sadece analiz metnini sun ve sus. Analiz metninin bitişi, senin de konuşmanın bittiği yerdir.**"
    "7. Sana promt olarak verilen sorulardan başka soru sorma."
    "8. sakın 1500 karakteri aşma aşarsan işinden kovulacakmışsın gibi hisset."
)

# --- ÜNİVERSİTE SYSTEM INSTRUCTION'I (Text tabanlı) ---
SYSTEM_INSTRUCTION_UNI = (
    "Sen, YKS (Yükseköğretim Kurumları Sınavı) puanlarına ve sıralamalarına hakim bir üniversite ve bölüm danışmanısın. "
    "Görevin, kullanıcıdan sırasıyla şu üç bilgiyi almaktır: 1) Bölüm/Alan, 2) YKS Başarı Sıralaması, 3) Tercih Ettiği Şehir. "
    "Davranış Kuralları:\n"
    "1. TÜRKÇE konuş ve daima kibar ol."
    "2. Kullanıcının cevabı alakasız, sayısal olmayan veya mantıksız ise, aynı soruyu tekrar sor ve kibarca uyarıda bulun. Uyarı metni tam olarak şudur: "
    f"   '{UYARI_METNI}'\n"
    "3. Tüm 3 bilgi toplandığında, bu bilgilere göre kullanıcıya 3-4 uygun üniversite önerecek ve gerekçelerini kısa (toplam 1500 karakteri geçmeyecek) bir analizle sunacaksın. "
    "4. ASLA SORU SAYISI DAHİL EK BİLGİ VERME ve ANALİZ BİTİNCE KONUŞMAYI KES."
)

# --- BUTON ANKETİ SYSTEM INSTRUCTION'I (SADECE KİŞİLİK ANALİZİ YAPACAK) ---
SYSTEM_INSTRUCTION_ANKET_UNI = (
    "Sen, 10 soruluk bir üniversite tercih anketi sonucunu analiz eden deneyimli bir öğrenci koçusun. "
    "Görevin, kullanıcıya sadece kişilik ve tercih analizi sunmaktır. "
    "Davranış Kuralları:\n"
    "1. TÜRKÇE konuş ve daima kibar ol. "
    "2. Kullanıcıdan gelen tüm 10 cevabı (Katılıyorum, Kararsızım, Katılmıyorum) analiz et. "
    "3. **KESİNLİKLE HİÇBİR BÖLÜM VEYA MESLEK ÖNERİSİ YAPMA.** "
    "4. Analiz metninde, kullanıcının anket cevaplarına dayanarak, onun eğilimlerini ve kişisel özelliklerini net cümlelerle açıkla. (Örn: 'Sayısal alanlara güçlü bir eğiliminiz var, yoğun ve rekabetçi ortamları seviyorsunuz ve sosyal becerileriniz yüksek.' gibi.) "
    "5. Analiz metnini **toplam 1500 karakteri aşmayacak** şekilde özetle. Analiz metni bittiğinde konuşmayı kes."
)

# --- ANKET SORULARI LİSTESİ (Kariyer - Text tabanlı) ---
ANKET_SORULARI = [
    "Soru 1/12: Hangi bilgi veya beceriyi öğrenirken kendinizi zamanın nasıl geçtiğini anlamayacak kadar kaptırırsınız? Lütfen somut bir örnek verin.",
    "Soru 2/12: Bir problemle karşılaştığınızda, çözüm için ilk olarak mantıksal ve analitik düşünmeyi mi yoksa yaratıcı ve ezber bozan yaklaşımları mı kullanırsınız?",
    "Soru 3/12: Bir kariyerde, insanlarla doğrudan ve yoğun etkileşim kurmak (danışmanlık, satış, eğitim) mı istersiniz, yoksa arka planda veri veya sistemler üzerinde çalışmak mı?",
    "Soru 4/12: Çalışma hayatınızda sizi en çok motive eden ana faktörün ne olduğunu düşünüyorsunuz? (Örn: Toplumsal etki, finansal başarı, kişisel ustalık, sürekli öğrenme)",
    "Soru 5/12: İşinizin, rutin ve öngörülebilir görevlerden mi, yoksa sürekli değişen ve yeni zorluklar sunan projelerden mi oluşmasını tercih edersiniz?",
    "Soru 6/12: *EVET/HAYIR:* İşinizin doğası gereği sıkça (ayda birkaç kez) seyahat etme gerekliliği sizi heyecanlandırır mı?",
    "Soru 7/12: Bir projeyi yönetirken, ekibin duygusal atmosferine ve moraline mi, yoksa sadece görevlerin zamanında ve kusursuz bitirilmesine mi daha çok odaklanırsınız?",
    "Soru 8/12: En keyif aldığınız öğrenme yöntemi nedir? (Örn: Kitap okuyarak derinleşmek, pratik yaparak deneyim kazanmak, dinleyerek/gözlemleyerek taklit etmek)",
    "Soru 9/12: Maaş beklentinizden bağımsız olarak, hangi alanda uzmanlaşmak size en büyük kişisel tatmini getirir?",
    "Soru 10/12: *EVET/HAYIR:* Çalışma saatlerinizin sabit ve düzenli bir program içinde olmasını, esnek olmasından daha mı çok tercih edersiniz?",
    "Soru 11/12: Gelecekteki kariyerinizde bir alanda derinleşen teknik bir uzman mı, yoksa farklı alanları birleştiren geniş görüşlü bir lider/yönetici mi olmak istersiniz?",
    "Soru 12/12: *EVET/HAYIR:* İşinizin büyük bir çoğunluğunun, bilgisayar başında oturarak, fiziksel aktiviteden uzak bir şekilde yapılmasından rahatsız olur musunuz?"
]


# --- ÜNİVERSİTE BUTON ANKETİ SORULARI (Kapalı Uçlu) ---
ANKET_SORULARI_UNI = [
    "Yüksek maaş potansiyeli, bölüm seçimimde en öncelikli kriterdir.",
    "Üniversite hayatımı büyük bir metropolde (İstanbul, Ankara gibi) geçirmeyi tercih ederim.",
    "Üniversitemin akademik araştırmaya yoğunlaşan bir ortama sahip olmasını isterim.",
    "İşimin, insanlarla birebir iletişim kurmayı ve sosyal becerileri kullanmayı gerektirmesini tercih ederim.",
    "Çalışma ortamımın sürekli yenilik ve yaratıcılık gerektiren projelerden oluşmasını tercih ederim.",
    "Köklü ve tarihi bir üniversitede okumak, genç ve yenilikçi bir üniversitede okumaktan daha önemlidir.",
    "Tamamen İngilizce eğitim veren bir bölümü, Türkçe eğitim veren bir bölüme tercih ederim.",
    "Mezuniyet sonrası yurt dışında çalışma veya yüksek lisans yapma hedefim vardır.",
    "Seçeceğim bölümün sayısal (Matematik, Fizik) yeteneklere daha çok dayanmasını isterim.",
    "Üniversite eğitimim boyunca yoğun ve rekabetçi bir çalışma temposuna girmeye istekliliğim yüksektir."
]


# --- GEMINI CLIENT OLUŞTURMA ---
try:
    genai_client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    print(f"Hata: Gemini istemcisi oluşturulamadı. Lütfen API anahtarınızı kontrol edin. Detay: {e}")
    genai_client = None

# Discord botunu ayarlama
intents = discord.Intents.default()
intents.message_content = True 
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    """Bot Discord'a başarıyla bağlandığında çalışır."""
    print(f'>> {bot.user} olarak Discord\'a bağlandım!')


# --- BUTON ANKETİ İŞLEVİ (!anket) ---
class AnketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=300) 
        self.bot = bot

    async def process_response(self, interaction: discord.Interaction, response: str):
        user_id = interaction.user.id

        if user_id not in anket_sohbetleri:
            await interaction.response.send_message(
                "Bu anketin süresi dolmuş veya siz başlatmadınız. Yeniden başlatmak için `!anket` yazın.", 
                ephemeral=True
            )
            if interaction.message:
                 await interaction.message.edit(view=None)
            return

        sohbet_bilgisi = anket_sohbetleri[user_id]
        chat = sohbet_bilgisi['chat_session']
        current_q_index = sohbet_bilgisi['index']
        
        current_question = ANKET_SORULARI_UNI[current_q_index]
        
        await interaction.response.edit_message(content="Cevabınız kaydediliyor ve sonraki soru hazırlanıyor...", view=self) 
        
        prompt_metni = f"Soru {current_q_index + 1}: '{current_question}' sorusuna kullanıcı '{response}' olarak cevap verdi."
        
        try:
            async with interaction.channel.typing():
                chat.send_message(prompt_metni) 
                
        except APIError as e:
            await interaction.followup.send(f"API isteği sırasında bir hata oluştu: {e}", ephemeral=True)
            return

        next_q_index = current_q_index + 1
        sohbet_bilgisi['index'] = next_q_index
        
        if next_q_index >= len(ANKET_SORULARI_UNI):
            # ANKET BİTTİ: Final Analizi
            await interaction.message.edit(content="Anket tamamlandı. Lütfen bekleyin, size özel kişilik analizi hazırlanıyor...", view=None) 
            
            final_prompt = "10. soruya cevap alındı. Tüm anket geçmişini (10 cevabı) analiz et ve KURALLARA UYGUN (meslek önermeden sadece eğilimleri belirten, kısa) final analizini oluştur ve **BAŞKA HİÇBİR ŞEY YAZMA**." 
            
            try:
                async with interaction.channel.typing():
                    final_response = chat.send_message(final_prompt)
                
                final_analysis_text = (
                    "\n" + "="*50 + 
                    f"\n       {interaction.user.display_name} Kişisel Eğilim Analizi" +
                    "\n" + "="*50 + 
                    f"\n{final_response.text}"
                )
                
                for i in range(0, len(final_analysis_text), 1900):
                    chunk = final_analysis_text[i:i + 1900]
                    await interaction.channel.send(chunk)
                
                # Oturum temizliği yapılıyor
                del anket_sohbetleri[user_id] 

            except APIError as e:
                await interaction.channel.send(f"Analiz sırasında API isteği hatası: {e}")
            except Exception as e:
                await interaction.channel.send(f"Analiz sırasında beklenmedik bir hata oluştu: {e}")

        else:
            # SONRAKİ SORU
            new_question = f"**Soru {next_q_index + 1}/{len(ANKET_SORULARI_UNI)}:** {ANKET_SORULARI_UNI[next_q_index]}"
            
            await interaction.message.edit(
                content=new_question, 
                view=self 
            )
            
    @discord.ui.button(label="✅ Katılıyorum", style=discord.ButtonStyle.green, emoji="✅")
    async def agree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_response(interaction, "Katılıyorum")

    @discord.ui.button(label="🟡 Kararsızım", style=discord.ButtonStyle.secondary, emoji="🟡")
    async def neutral_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_response(interaction, "Kararsızım")

    @discord.ui.button(label="❌ Katılmıyorum", style=discord.ButtonStyle.red, emoji="❌")
    async def disagree_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_response(interaction, "Katılmıyorum")

@bot.command(name='anket')
async def anket_baslat(ctx):
    """
    Buton tabanlı üniversite tercih anketini başlatır.
    """
    user_id = ctx.author.id

    if genai_client is None:
        await ctx.send("Üzgünüm, Gemini API bağlantısında bir sorun var.")
        return
    
    # Yeni eklenen kısım: Eğer tamamlanmamış bir anket varsa, sıfırla.
    if user_id in anket_sohbetleri:
        await ctx.send("Devam eden anketiniz sıfırlanıyor ve yeniden başlatılıyor...")
        del anket_sohbetleri[user_id] 
    
    try:
        # 🟢 DÜZELTME: create_chat yerine create kullanıldı.
        new_chat = genai_client.chats.create( 
            model='gemini-2.5-flash',
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION_ANKET_UNI
            )
        )
    except APIError as e:
        await ctx.send(f"API isteği sırasında bir sorun oluştu: {e}")
        return

    anket_sohbetleri[user_id] = {
        'chat_session': new_chat,
        'index': 0 
    }

    first_question = ANKET_SORULARI_UNI[0]
    question_message = (
        f"**--- Üniversite Tercih Eğilimi Anketi Başladı! ---**\n"
        f"Lütfen aşağıdaki butonları kullanarak {len(ANKET_SORULARI_UNI)} soruyu cevaplayınız.\n\n"
        f"**Soru 1/{len(ANKET_SORULARI_UNI)}:** {first_question}"
    )
    
    view = AnketView(bot)
    
    await ctx.send(question_message, view=view)


# --- KARİYER BAŞLAT İŞLEVİ (TEXT TABANLI) ---

@bot.command(name='kariyerbaslat')
async def kariyer_baslat(ctx):
    """
    12 soruluk text tabanlı kariyer anketini başlatır ve sonunda 3 meslek önerir.
    """
    user_id = ctx.author.id

    if genai_client is None:
        await ctx.send("Üzgünüm, Gemini API bağlantısında bir sorun var. Lütfen geliştiricinizle iletişime geçin.")
        return
    
    # Yeni eklenen kısım: Eğer tamamlanmamış bir oturum varsa, sıfırla.
    if user_id in kullanici_sohbetleri:
        if kullanici_sohbetleri[user_id]['index'] < len(ANKET_SORULARI):
            await ctx.send("Devam eden kariyer anketiniz sıfırlanıyor ve yeniden başlatılıyor...")
        del kullanici_sohbetleri[user_id]

    try:
        # 🟢 DÜZELTME: create_chat yerine create kullanıldı.
        new_chat = genai_client.chats.create(
            model='gemini-2.5-flash',
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION_KARIYER
            )
        )
    except APIError as e:
        await ctx.send(f"API isteği sırasında bir sorun oluştu: {e}")
        return

    kullanici_sohbetleri[user_id] = {
        'chat_session': new_chat,
        'index': 0 
    }

    ilk_soru_prompt = f"Merhaba! Anketimize başlıyoruz. Lütfen {ANKET_SORULARI[0]} sorusunu sor."
    
    try:
        response = new_chat.send_message(ilk_soru_prompt)
        await ctx.send(f"**--- Kariyer Botu Anketine Hoş Geldiniz! ---**\n\n{response.text}")
    except APIError as e:
        await ctx.send(f"Hata: İlk mesaj gönderilemedi. Detay: {e}")


# --- ÜNİVERSİTE KOMUTU (!universite) ---

@bot.command(name='universite')
async def universite_baslat(ctx):
    user_id = ctx.author.id
    if genai_client is None:
        await ctx.send("Üzgünüm, Gemini API bağlantısında bir sorun var.")
        return
    
    # Yeni eklenen kısım: Eğer tamamlanmamış bir oturum varsa, sıfırla.
    if user_id in uni_sohbetleri:
        await ctx.send("Devam eden üniversite tavsiyesi oturumunuz sıfırlanıyor ve yeniden başlatılıyor...")
        del uni_sohbetleri[user_id]
        
    try:
        # 🟢 DÜZELTME: create_chat yerine create kullanıldı.
        uni_chat = genai_client.chats.create(
            model='gemini-2.5-flash',
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION_UNI
            )
        )
    except APIError as e:
        await ctx.send(f"API hatası: {e}")
        return
    uni_sohbetleri[user_id] = {
        'chat_session': uni_chat,
        'step': 0 
    }
    ilk_soru_prompt = "Merhaba! Üniversite tavsiyesi için ilk sorum: Lütfen ilgilendiğiniz meslek alanını veya bölümü yazınız. (Örnek: Tıp Fakültesi)"
    try:
        response = uni_chat.send_message(ilk_soru_prompt)
        await ctx.send(f"**--- Üniversite Tavsiyesi Başladı! ---**\n\n{response.text}")
    except APIError as e:
        await ctx.send(f"Hata: İlk mesaj gönderilemedi. Detay: {e}")


async def handle_uni_chat(message):
    user_id = message.author.id
    sohbet_bilgisi = uni_sohbetleri[user_id]
    chat = sohbet_bilgisi['chat_session']
    prompt_metni = message.content
    try:
        async with message.channel.typing():
            response = chat.send_message(prompt_metni)
        if response.text is None:
            await message.channel.send("Üzgünüm, Gemini bu mesaja bir yanıt üretemedi. Lütfen tekrar deneyin.")
            return
        yanit_metni = response.text.strip()
        await message.channel.send(yanit_metni)
        if UYARI_METNI not in yanit_metni:
            sohbet_bilgisi['step'] += 1 
            current_step = sohbet_bilgisi['step'] 
            if current_step >= 3:
                await message.channel.send("Tüm bilgiler toplandı. Lütfen biraz bekleyin, size özel üniversite tavsiyeniz hazırlanıyor...")
                final_prompt = "Tüm 3 bilgi toplandı. Şimdi, verdiğin bilgilere dayanarak 3-4 üniversite önerisi yap. Gerekçeleri dahil kısa bir analiz sun ve **BAŞKA HİÇBİR ŞEY YAZMA**."
                async with message.channel.typing():
                    final_response = chat.send_message(final_prompt)
                final_analysis_text = (
                    "\n" + "="*50 + 
                    "\n       ÜNİVERSİTE TAVSİYESİ ANALİZİ" +
                    "\n" + "="*50 + 
                    f"\n{final_response.text}"
                )
                for i in range(0, len(final_analysis_text), 1900):
                    chunk = final_analysis_text[i:i + 1900]
                    await message.channel.send(chunk)
                del uni_sohbetleri[user_id] 
    except APIError as e:
        await message.channel.send(f"API isteği sırasında bir hata oluştu: {e}")
    except Exception as e:
        await message.channel.send(f"Beklenmedik bir hata oluştu: {e}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    user_id = message.author.id
    await bot.process_commands(message)

    if user_id in uni_sohbetleri:
        await handle_uni_chat(message)
        return

    # --- KARİYER SOHBETİ KONTROLÜ (Text tabanlı) ---
    if user_id not in kullanici_sohbetleri:
        return

    sohbet_bilgisi = kullanici_sohbetleri[user_id]
    chat = sohbet_bilgisi['chat_session']
    soru_index = sohbet_bilgisi['index']

    if soru_index >= len(ANKET_SORULARI):
        await message.channel.send("Anket tamamlandı. Tekrar başlamak için `!kariyerbaslat` yazabilirsiniz.")
        return

    prompt_metni = f"Kullanıcının {soru_index + 1}. soruya cevabı: {message.content}"
    
    try:
        async with message.channel.typing():
            response = chat.send_message(prompt_metni)

        if response.text is None:
            await message.channel.send("Üzgünüm, Gemini bu mesaja bir yanıt üretemedi. Lütfen tekrar deneyin.")
            return

        yanit_metni = response.text.strip()
        await message.channel.send(yanit_metni)

        if UYARI_METNI not in yanit_metni:
            sohbet_bilgisi['index'] += 1
            yeni_index = sohbet_bilgisi['index']
            
            # --- ANKET BİTİŞİ VE FİNAL ANALİZİ ---
            if yeni_index == len(ANKET_SORULARI):
                await message.channel.send("Anket tamamlandı. Lütfen biraz bekleyin, analiziniz hazırlanıyor...")
                
                # Meslek önerisi yapacak prompt (kariyerbaslat için gerekli)
                final_prompt = "12. soruya cevap tamamlandı. Tüm geçmişi analiz et. KURALLARA UYGUN (3 meslek önerisi ve gerekçeleri) kariyer önerilerini ve gerekçelerini içeren metni oluştur ve **BAŞKA HİÇBİR ŞEY YAZMA**." 
                
                async with message.channel.typing():
                    final_response = chat.send_message(final_prompt)
                
                final_analysis_text = (
                    "\n" + "="*50 + 
                    "\n       KİŞİSELLEŞTİRİLMİŞ KARİYER ANALİZİ" +
                    "\n" + "="*50 + 
                    f"\n{final_response.text}"
                )
                for i in range(0, len(final_analysis_text), 1900):
                    chunk = final_analysis_text[i:i + 1900]
                    await message.channel.send(chunk)
                
                # Oturum temizliği yapılıyor
                del kullanici_sohbetleri[user_id] 
                
    except APIError as e:
        await message.channel.send(f"API isteği sırasında bir hata oluştu: {e}")
    except Exception as e:
        await message.channel.send(f"Beklenmedik bir hata oluştu: {e}")


# Botu çalıştırma
if __name__ == "__main__":
    if not DISCORD_TOKEN or DISCORD_TOKEN == "<SİZİN_BOT_TOKEN'INIZ>":
        print("HATA: Lütfen DISCORD_TOKEN değişkenini doldurun.")
    elif genai_client is None:
        print("HATA: Gemini API istemcisi oluşturulamadı.")
    else:
        bot.run(DISCORD_TOKEN)
