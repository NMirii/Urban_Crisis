# AI istifadəsi haqqında bəyannamə
Tarix: 15 noyabr 2026. Layihə: Urban Crisis & Crowd Evacuation Engine.

## İstifadə edilən alət və həcm
ChatGPT daxilində Codex kodlaşdırma agenti istifadə edilib. Bu təqdimatdakı ilkin kod, frontend, testlər və sənədlər AI tərəfindən yaradılıb. İnsan tərəfindən tam code review və texniki müdafiə yoxlamasının aparıldığı iddia edilmir. Komanda təqdim etməzdən əvvəl yoxlamanı tamamlamalı və aşağıdakı qeydləri öz real fəaliyyəti ilə yeniləməlidir.

| Mərhələ | AI istifadəsi | Yoxlama |
|---|---|---|
| Tələblər | İki modulun davranışa və qaydalara çevrilməsi | 90% və >95% fərqi ayrıca test |
| Arxitektura | Python, SQLite, ayrıca domen mühərriki seçimi | Lokal işə salınma və HTTP testləri |
| Kod | Dijkstra, Haversine, SOS klasteri, API, UI | 24 avtomatik test; JS sintaksisi |
| Testlər | Domen və inteqrasiya ssenarilərinin yazılması | Testlər həqiqətən icra edilib |
| Sənədlər | README, texniki izah, bəyannamə | Mövcud tətbiqin davranışı ilə uyğunlaşdırılıb |
| Challenge Drop | Konfiqurasiya nöqtələri hazırlanıb | Faktiki Drop verilməyib, həll iddiası yoxdur |

## Prompt izi
Ayrıca başqa AI sisteminə prompt göndərilməyib. Əsas prompt komandanın bu söhbətdə təqdim etdiyi Azərbaycan dilində tapşırıq mətni olub. Aşağıdakılar həmin promptdan seçilmiş birbaşa fraqmentlərdir; tam transkript deyil:

> “urban crisis & crowd evacuation engine mikro sisteminin islek prototipinin hazilamalidir”

> “5 deqiqe erzinde en az 5 ferqli sos siqnali”

> “toplanis menteqesinin dolulugu 95% kecerse”

> “qerarin icrasini bir klikle tesdiqlemek”

Agent bu prompt əsasında fayl yazma və test işə salma əmrləri yaradıb; bunlar ayrıca insan promptları kimi təqdim edilmir. Qərarlar: xarici xəritə əvəzinə icazə verilən simulyasiya; fərqli siqnallar üçün unikal vətəndaş; konfiqurasiya edilən hədlər; lokal standart kitabxana stack-i. Sonradan başqa AI aləti və ya prompt istifadə olunarsa komanda tarix, alət, tam prompt, dəyişən fayllar və yoxlama nəticəsini buraya əlavə etməlidir.

## Nəzarət və aşkarlanmış problemlər
İlk test-faylı yazma əmri səhv nisbi qovluğa yönəldiyi üçün fayl yaranmadı; yol düzəldildi və 24 test keçirildi. Brauzer sınağında əvvəl Playwright browser binary çatışmadı, sistem Chromium-u isə proses/socket məhdudiyyəti ilə başlamadı. Buna görə UI testinin uğurlu keçdiyi iddia edilmir. Docker build işlədilməyib. Runtime sistemdə LLM/AI qərar qəbul etmir; bütün alarmlar açıq deterministik qaydalarla hesablanır. Kodda real vətəndaş məlumatı və API sirri yoxdur.

## Komandanın tamamlamalı olduğu hissə
- Baxan komanda üzvü: [doldurun]
- İnsan code review tarixi və qeydləri: [doldurun]
- Lokal brauzer demo nəticəsi: [doldurun]
- Faktiki Challenge Drop promptları və dəyişiklikləri: [doldurun]
