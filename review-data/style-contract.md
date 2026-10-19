# Illustration contract — user confirmed, 3 October 2026

## Final approval — 7 October 2026

The user explicitly selected #151 candidate `151-f-v1` («چرخ همونه؛ حالا خودم بلدم!») as `approved` in the live review and reported «بازخورد ۱۵۱ ثبت شد». No new revision comment accompanied that approval. The exact original-quality file is saved as `Images/151.png`; approval, image hash and prompt are retained in `review-data/project-state.json`. This accepted illustration is an additional positive style reference for future work. Keep the user's neutral-body and consistent-clothing refinements from 7 October even when using this image as a reference. Other #151 candidates remain preserved but are not approved.

The user's pasted Persian example prompt for #133 takes precedence over inferred details in style-study.md. Its 16:9 horizontal three-panel layout is scene-specific; choose the next sentence's aspect ratio and panel count to serve its story.

## Invariants

- Authentic hand-painted watercolor at a moderate, restrained strength, matching references/watercolor-medium-2026-10-03.jpg. Show watercolor inside the characters’ heads, torsos, limbs and hands as well as the setting and outer edges: broad softly irregular overlapping translucent washes, varied pigment density, luminous paper and subtle pooling. Avoid uniform fine marker/pencil grain, repeated embossed/crystalline texture, excessive staining, splashes or heavy mottling. Keep clear locally colored contour lines. Never flat/vector, glossy/3D, or photorealistic.
- Clean white paper margins around the painting; pigment does not touch the file edges. Fully include bodies, feet and important objects.
- Balanced simple adult bodies with proportions matched to the relevant book reference, without excessively stretched or thin limbs, chunky round torsos, or chibi proportions. Female and male figures retain a neutral body build: no bust, pinched waist, prominent hips or buttocks, or gendered bulges and indentations. Eyelashes are the main female cue; the user's 7 October clarification allows very slight extra delicacy while keeping the neutral silhouette. Fully circular heads, never oval. No necks: heads join directly to the upper torso/shoulders, as explicitly stated by the user in the C-v3 request.
- Every visible hand has exactly three fingers and one thumb. Simplify by pose or occlusion only when natural; never use a mitten as a substitute for the stated design.
- A soft local-color crescent contact shadow immediately below the round head on the upper torso distinguishes head and body. The head still directly joins the shoulders: no neck segment, collar or floating gap.
- Minimal but expressive eyes, eyebrows and mouth. Match the actual reference eyes: modest dark ovals with a SMALL white light reflection INSIDE when appropriate; no surrounding white sclera or a separate pupil on a large white eyeball. The user's clarification expressly allows the tiny interior glint. Do not remove it as a blanket rule or create blank scary eyes. Female eyelashes are a few fine short upper-outer curved strokes, matching examples 110 and 131; no heavy doll-like lash fans. No noses, ears or hair in the ordinary cast. Character identity, color and proportions remain consistent through panels.
- All in-image writing is Persian, with correct connected letters and RTL direction. Use only short necessary text. Dialogue is natural colloquial Persian, as requested in the C-v4 feedback (for example «خودم رو» rather than «خودم را»). Speech tails and thought trails clearly belong to their speaker.
- Warm, kind, bright, human humor; gentle surprise and emotional meaning. Family friendly. Avoid ridicule and heavy moralizing.
- Settings feel inhabited but restrained. Plants, flowers and decorative props are sparse and purposeful.
- Horizontal story sequences proceed right to left, vertical sequences top to bottom; no heavy panel borders. Clear continuity and readable cause and effect.

## Story method

Interpret the underlying idea, give a character a concrete situation and action, and show a surprising consequence or meaningful change. The art must communicate without an outside explanation. Humor belongs to the scene. Do not merely draw a literal translation or quote the advice inside the image.

For #133 the compliment is genuinely made while the baker cannot hear it; it circulates; it returns as heart-shaped bread. This causal precision is as important as visual polish.

For #151, follow the user's 10 October clarification: the central story is becoming a better human through the process of effort, rather than making money, possessions, rank or status the purpose of that effort. Increased physical strength, professional skill or confidence alone is insufficient for this commissioned interpretation. Show a change of character through choices and conduct toward people; make the difference between the two aims visible. Do not invent a blanket claim that receiving income or owning things is bad.

## Review and learning

- Pilot: five distinct narrative mechanisms for #151. Wait for the user's style feedback before launching the first ten-sentence production wave.
- Production: four distinct ideas per sentence, usually ten sentences per wave. Regenerate rejected sets and revise chosen candidates using the user's exact comments.
- `approved`: explicitly final; may be copied to Images. `revise`: a target needing changes, never final; the last `chosenIdeaId` can be the most recent edit target and is not evidence of preference over other commented images. Read every current-wave idea note and its submission history. `rejected`: retry whole sentence. `pending`: no decision.
- Preserve exact workbook wording in the review. Explicit general preferences stated by the user become rules immediately; only preferences inferred from choices remain hypotheses until supported by further feedback.
- Keep prompts, image revisions, feedback and approval history. Never overwrite an existing book image silently.
- For long two-page advice, use a small foreshadow vignette and a complete payoff illustration, not a duplicated thumbnail.

## Direct feedback for #151 — 3 October 2026

- A: the user described the heads as oval and bodies too stretched, identified a two-finger wooden hand and did not find the idea aligned with the sentence. A later received the body/hand and medium revisions in A-v2; it has not been approved. Preserve the user's conceptual objection.
- C, submitted request ea5d1a22-c866-4fc5-997c-198f790be95f: remove the wall shadow, shorten both figures, add eyelashes to the green figure and replace the carpenter interior with a home. These four exact changes were applied in C-v2; the original dialogue and watercolor identity were retained.
- Shadow removal, the home interior and the green figure's eyelashes are C-specific choices, not universal restrictions on the book. Feedback on exaggerated elongation occurred for both A and C and should guide closer reference matching in subsequent prompts.
- C-v2 is ready for review, not automatically approved. Further comments must target its new version ID.

- C, submitted request 03e3f29e-0cf5-45f6-9177-c028866b19e4: remove both necks and separate the wall from the sky. C-v3 applies both corrections, preserves C-v2 and all earlier corrections, and awaits review. The user phrased no necks as a rule for their characters; retain that as a global design requirement. The wall/sky architecture fix is specific to this scene.

## Direct medium calibration — 3 October 2026

The user supplied the office/hourglass image as a paint-medium reference, not a story or hand-anatomy reference. Match its moderate watercolor visible inside the bodies and its soft head/torso shadow. Its three-digit hand defect must not be reproduced: exactly three fingers plus one thumb remains required, including sculptures and gloves. Applied to all five current #151 candidates in pilot-151-v4 and retained for all future prompts. Prior book artwork and every published candidate remain preserved; the new revisions await explicit review.

## اصلاحات قطعی برای پنج ایدهٔ تازهٔ جملهٔ ۱۵۱

- نمونه‌های حاشیه: ۱، ۶۸ و ۷۰. نمونه‌های تناسب و رنگ‌آمیزی بدن: ۳۰، ۱۱۳، ۹۷، ۱۱۰، ۸۴، ۱۳۱ و ۱۴۸. شمارهٔ ۰۷ اشتباه تایپی بود؛ ۹۷ درست است. شمارهٔ ۷۰ برای حاشیه درست است.
- حاشیه گاهی با درخت، برگ، زمین یا پایان طبیعی ضربه‌های قلم‌مو شکل می‌گیرد؛ گاهی باز و ناپیوسته است. همیشه فضای سفید بیرون تصویر حفظ می‌شود؛ همهٔ تصاویر یک محوشدگی مستطیلی یکسان ندارند.
- نزدیک‌تر بودن سبک ایدهٔ «چی با خودت می‌بری؟» ترجیح نسبی است؛ به معنی تأیید نهایی آن تصویر یا ایده نیست.
- فرم بدن زنانه ممنوع است. اندام ساده و خنثی برای همهٔ جنسیت‌ها به‌کار می‌رود: بدون سینه یا باسن برجسته، کمر باریک و منحنیِ برجستگی/فرورفتگی. مژه نشانهٔ اصلی تفکیک است؛ ظرافت بسیار کم هم مجاز است، به شرط حفظ فرم خنثی بدن. تناسب باید میانه باشد؛ نه گرد و قلمبه و نه لاغر و بیش از حد کشیده.
- «سفیدی چشم» یعنی بخش سفیدِ چشم دور مردمک؛ برق کوچک داخل چشم ممنوع نیست. برداشت قبلیِ حذف کامل برق اشتباه بود و کنار گذاشته شد. چشم و مژه مستقیماً با نمونه‌های ۱۱۰ و ۱۳۱ تطبیق داده می‌شوند.
- داستان با مشاهدهٔ مستقیم قابل فهم باشد. پیوستگیِ هویت شخصیت و رابطهٔ علت و نتیجه حفظ شود. ثابت‌ماندن شیء یا موقعیت فقط وقتی لازم است که همان شیء و موقعیت موضوعِ تغییر باشند؛ برای گذر چند دهه، محیط و اشیای تکراریِ بدون تغییر باورپذیر نیستند. طنز از یک موقعیت سادهٔ انسانی بیاید. توضیح فارسیِ ایده و پیام آن در صفحهٔ مرور درج شود.

## تازه‌ترین بازخورد دربارهٔ خیاط نارنجی

- نسخه‌ای که مستقیماً از نقاشی ۱۳۱ بازسازی شد، به گفتهٔ کاربر «خیلی بهتر» است. این ترجیح نسبی، تأیید نهایی تصویر نیست. برای ادامه، طراحی و رنگ‌گذاری خودِ نقاشی مرجع حفظ شود و داستان، اشیا و محیط با ویرایش آن تغییر کنند؛ خروجی‌های ناموفقِ قبلی مبنای بازطراحی نباشند.
- خط دور بدن و سر سیاه نیست؛ از خانوادهٔ رنگ همان بدن، با تیرگی بیشتر است. برای نارنجی از نارنجی سوخته، برای آبی از آبی تیره‌تر، و برای دیگر رنگ‌ها از رنگ محلی تیره‌تر استفاده شود. این قاعده شامل چشم و نوشته‌ها نمی‌شود.
- سر باید یک دایرهٔ ساده باشد؛ بیضی، فک، چانه و تخت‌شدن قوس پایین ممنوع است. تغییر جهت نگاه یا چرخش اجزای صورت، محیط دایره را تغییر نمی‌دهد.
- رنگ‌آمیزی آبرنگی نسخهٔ نزدیک‌تر حفظ شود؛ اصلاح هندسه نباید به ریزبافت یکنواخت، رنگ ماژیکی یا حجم‌پردازی براق برگردد.

## تثبیت سبک و پوشش برای تولید بعدی

- کاربر سبک پنج طرح تازهٔ جملهٔ ۱۵۱ را پسندیده است. این تأیید سبک، تأیید نهاییِ تک‌تک تصاویر برای ذخیره در پوشهٔ کتاب نیست؛ انتخاب هر تصویر جداگانه در روند مرور ثبت می‌شود.
- در صحنه‌ای که آدمک‌ها پوشش خاصی ندارند، یک آدمک به‌تنهایی لباس ویژه نداشته باشد؛ تفاوت ناخواسته ممکن است بقیه را برهنه جلوه دهد. پیش‌بند مجاز است. پوشش دیگری فقط زمانی استفاده شود که خودِ موضوع صحنه آن را لازم می‌کند و با پوشش سایر شخصیت‌ها هماهنگ باشد.
- برای آزمایش سایت از داده و تصمیم‌های جدا از بازخورد واقعی استفاده شود. تولید گسترده پس از یک دور کاملِ انتخاب، اصلاح، رد و تحویل فایل نهایی آغاز شود.

## راهنمای مستقیم کاربر برای رنگ فرم و روایت ۸ اکتبر ۲۰۲۶

این بخش از درخواست مستقیم کاربر می‌آید و برای طراحی‌های بعدی لازم‌الاجراست. سه تصویر ۱۳، ۶۰ و ۸۰ مرجع ایده‌پردازی‌اند؛ استفاده از آنها به معنی بازسازی همان موقعیت‌ها در همهٔ جمله‌ها نیست. تصاویر و بازخوردهای موج‌های قبلی محفوظ می‌مانند.

- طیف رنگ آدمک‌ها متنوع باشد؛ استفادهٔ تکراری از زرد، نارنجی و آبی پیش‌فرض نباشد. رنگ می‌تواند به خواندن موقعیت کمک کند: قرمز برای عصبانیت، بنفش برای انتظار، زرد برای انرژی، صورتی برای لطافت و حساسیت، سبز برای نگرش مثبت و آبی برای خونسردی، از مثال‌های کاربر هستند. این مثال‌ها قرارداد اجباری و جهانی برای هر رنگ نیستند؛ رنگ برای زیبایی و تضاد هم مجاز است. معنا باید با حالت چهره، کنش و موقعیت نیز روشن باشد و به دانستن یک رمز رنگی وابسته نشود.
- رنگ و هویت شخصیت در قاب‌های یک داستان ثابت بماند. تغییر رنگ همان شخصیت فقط برای تغییرِ عمدی و واضحِ حال‌وهوا، با حفظ سایر نشانه‌های هویتش و تداوم کنش قابل استفاده است؛ تغییر بی‌دلیل رنگ باعث اشتباه در تشخیص شخصیت می‌شود.
- هنگام اضافه‌کردن مژه، همان چشم مرجع حفظ شود: اندازه، فرم سادهٔ بیضیِ تیره، محل، جهت و برق کوچک داخلی تغییر نکنند. فقط چند خط کوتاه و ظریف در لبهٔ بالاییِ بیرونی چشم افزوده شود. برای مؤنث‌کردن، چشم جدید، سفیدِ دور مردمک، چشم درشت یا بادبزن مژه طراحی نشود؛ فرم بدن نیز خنثی بماند.
- قالب پیش‌فرض تصویر مربع است. تعداد قاب از نیاز روایت می‌آید. اگر سه بخش یا امتداد صحنه در مربع خوانایی را کم می‌کند، مستطیل عمودی یا افقی مجاز است. برای استفاده از مربع، داستان یا اندازهٔ عناصر مهم فشرده و ناخوانا نشوند.
- مخاطب می‌تواند دوازده‌ساله و بدون آشنایی با استعارهٔ مورد نظر باشد. کتاب توضیح بیرونیِ ایده ندارد؛ توضیح فارسیِ سایت ابزار مرورِ صاحب کتاب است و نباید ضعف معنای تصویر را جبران کند.
- پیش از تولید، طرح را از دید چنین مخاطبی بررسی کن: در نگاه اول چه می‌بیند، علت و نتیجه را از کدام نشانه‌ها می‌فهمد، و آیا برداشت دیگری با همین نشانه‌ها سازگارتر است؟ اگر معنای مرکزی فقط پس از توضیح عامل قابل فهم می‌شود، ایده قبل از تولید بازنویسی یا کنار گذاشته شود. این بررسی، داوری عامل است؛ بدون آزمون انسانی ادعای سرعت درک قطعی نکن.
- خلاقیت در پیوند روشن و تازهٔ اشیا، کنش و پیام باشد، نه در پیچیدگی یا رمزی‌کردن تصویر. یک استعارهٔ اصلی و نشانه‌های ضروری کافی‌اند؛ مفهوم تازه و عمیق می‌تواند با روایت ساده منتقل شود.
- متن کوتاه فارسی داخل تصویر مجاز است و گاهی ضروری است، مثل برچسب «نفرت» و «سم کشنده» در ۶۰. این نوشته‌ها شیء یا موقعیت را روشن می‌کنند؛ نباید توضیح طولانیِ درس تصویر باشند یا تنها حاملِ پیام شوند.
- مقایسه و تغییر را دیدنی کن: وزن و ارتفاع در ۱۳، منبع سم و مسیر انتشار در بدنِ صاحب نفرت در ۶۰، و تداوم همان خرده‌آینه‌ها از شکستگی تا تابلوی رنگی در ۸۰. از قطع رابطهٔ بصریِ شیء اولیه و نتیجه پرهیز کن.
- چندقابی‌بودن ضروری نیست: در ۸۰ توپ و آینهٔ شکسته علت بحران را می‌رسانند، رنگ‌کردن تکه‌ها عمل شخصیت را، و تابلوی موزاییکی نتیجه را؛ هر سه در یک صحنه خوانده می‌شوند. قاب‌های اضافی فقط وقتی توالی را روشن‌تر می‌کنند به کار بروند.

## بازخورد مستقیم کاربر — ۱۰ اکتبر ۲۰۲۶، موج ۱۵۱ تا ۱۵۳

منبع: یادداشت جداگانهٔ هر ۱۲ تصویر در فایل دانلودی `feedback-regen-151-153-2026-10-08-v1.json` و نسخهٔ یکسان ذخیره‌شده در سرور. همهٔ این تصاویر درخواست اصلاح دارند؛ آخرین هدف ویرایش برای هر جمله انتخاب نهاییِ آن تصویر محسوب نمی‌شود. این بخش بر برداشت‌های قبلی عامل تقدم دارد.

- برای ۱۵۱، «شدن» به بهترشدنِ منش و کیفیت انسانی در فرآیند تلاش مربوط است. صرف قوی‌ترشدن، ماهرترشدن یا بااعتمادبه‌نفس‌ترشدن کافی نیست. دنبال پول، ثروت، جاه و مقام بودن نباید هدف اصلی داستان باشد. تغییر انسان باید در رفتار و انتخابش دیده شود؛ افزودن یک پاکت حقوق به گوشهٔ نقاشی این تقابل را نمی‌سازد.
- مخاطب کتاب بزرگسال است. قابل‌فهم‌بودن برای مخاطب دوازده‌ساله، مجوز تبدیل روایت به فضای مهدکودکی، اسباب‌بازی یا درس بسیار ابتدایی نیست. خلاقیت و عمق در روایت ساده حفظ شوند. اعتراض مستقیم به برجِ بلوک‌های ۱۵۲ به معنای ممنوعیت کلی هر بلوک یا بازی در کتاب نیست؛ آن موقعیت برای این جمله پذیرفتنی نبوده است.
- ته‌رنگ گونه، اگر استفاده شد، ملایم و نیمه‌شفاف با لبه‌های محو آبرنگی باشد. لکهٔ صورتیِ تخت، گرد، شارپ یا پررنگ از سبک مرجع خارج است؛ برای احساس، چشم و دهانِ مرجع تغییر نامتناسب نکنند.
- اتصال تنه، لگن خنثی و پاها و امتداد بدن در تمام وضعیت‌ها بررسی شود؛ میز، پیش‌بند یا اشیای جلویی نباید ناهماهنگیِ اندام را بپوشانند. بدن مؤنث همان قواعد خنثی را حفظ کند.
- جهت نگاه، اشاره و گفتار باید به یک موضوع سازگار مربوط باشند. قضاوت دربارهٔ شخص دیگر هم‌زمان با خیره‌شدن به کفش خود، بدون مرحلهٔ مجزای خودنگری، رابطهٔ روایت را خراب می‌کند.
- بازتاب آینه از جهت، زاویه، فرم و وضعیت بدن واقعی پیروی کند. برای نمایش چهره در آینه، شخصیت باید رو به آینه باشد؛ بازتابِ صورت وقتی پشت شخصیت به آینه است پذیرفتنی نیست. اگر لازم شد صحنه دوباره چیده شود؛ اصلاح صرفِ آدمک داخل آینه کافی نیست.
- در ۱۵۲، بندهای باز در شروع دویدن دیده شوند؛ گرهِ غیرعادیِ دو کفش به هم کنار خط پایان، روایت مورد نظر کاربر نیست. برج خودِ منتقد نیز در تصویر فعلی ضعف روشن ندارد و کل این ایده باید بازاندیشی شود.
- در ۱۵۳، حفظ رنگ و هویت شخصیت به معنی ثابت‌ماندن مصنوعیِ محیط، کیک، آلبوم، نیمکت یا وسایل در گذر چند دهه نیست. دورهٔ دوم باید تغییر زمان را باورپذیر کند. خمیدگیِ اندک و طبیعی بدن می‌تواند در کنار چند چروک و عینک نشانهٔ پیری باشد؛ بدن نباید دفرمه یا جنسیت‌دار شود.
- عکس‌های آلبوم باید رو به اشخاصی باشند که آن را نگاه می‌کنند؛ در طرح فعلی ۱۵۳-F باید ۱۸۰ درجه بچرخند. خوانایی برای بیننده توجیهِ جهت غلط نیست.
- دوچرخهٔ ۱۵۳-H با زاویه‌ای چیده شود که هر دو چرخ و ساختمان درست دوچرخه قابل تشخیص باشند؛ پنهان‌بودن چرخ در خروجی فعلی مشکل را برای کاربر حل نمی‌کند.
- تحلیل پیشنهادی عامل برای ۱۵۲: خودنگریِ دشوار، پذیرش سهم خود و پاداش ملموسِ اصلاح، فراتر از نشان‌دادن دورویی منتقد. تحلیل پیشنهادی عامل برای ۱۵۳: اثر واقعی دوستی میان نسل‌ها بر تجربه، نگاه و زندگی، فراتر از صرفاً کنار هم گذاشتن جوان و پیر. این دو تحلیل پیشنهاد عامل‌اند و تأیید تازهٔ کاربر محسوب نمی‌شوند.

## ثبت انتخاب نهایی و پرامپت — درخواست مستقیم ۱۰ اکتبر ۲۰۲۶

- هر تصویر انتخاب‌شدهٔ نهایی با بایت‌های فایل اصلی در پوشهٔ Images ذخیره و همان نسخه دانلود شود. طبق جابه‌جایی ستون‌ها به درخواست ۱۹ اکتبر ۲۰۲۶، پرامپت کامل مستقل انگلیسیِ تولید همان تصویر در ستون D فایل اصلی اکسل، مقابل شناسهٔ همان جمله، ثبت شود. ترجمه‌های فارسیِ پیشین در ستون C محفوظ‌اند.
- برای هر گزینه و هر نسخهٔ اصلاح‌شده، پیش از انتشار پرامپت مستقل کامل انگلیسی تهیه شود؛ متن کوتاه «این بخش تصویر قبلی را ویرایش کن» به‌جای آن کافی نیست. فقط متن‌های لازم داخل تصویر در این پرامپت به فارسی نقل شوند. پرامپت ویرایش و منشأ تصویر جداگانه محفوظ باشند.
- انتخاب ثبت‌شده و ذخیرهٔ نهایی کامل دو وضعیت جدا دارند: موفقیت فقط پس از بررسی تصویر و پرامپت اعلام شود. خطای ذخیره، نظر کاربر را پاک نکند؛ تلاش دوباره و نشانگر وضعیت در صفحه وجود دارند.
- جزئیات اجرایی و قرارداد متادیتا در `review-data/finalization-workflow.md` ثبت شده است.

## اصلاح مستقیم ۱۵۲، ایدهٔ بند کفش — ۱۰ اکتبر ۲۰۲۶

- تصحیح مستقیمِ ویس کاربر بر برداشت قبلی تقدم دارد: در قاب اول زرد هم مانند صورتی در حال دویدن روی همان مسیر باشد. در قاب دوم توقف می‌کند و به بندهای خودش نگاه می‌کند، سپس در قاب سوم همان محل توقف می‌نشیند. خودِ سطح ساده و جهت یکسان مسیر باید پیوستگی را آشکار کند؛ راه فرعی یا تغییر جهت مسیر پذیرفتنی نیست. برداشت قبلیِ ایستادن زرد در قاب اول نادرست بود.
- اصلاح بعدیِ مستقیم کاربر در چت: تابلوهای شروع و همهٔ نیمکت‌ها حذف شوند؛ چمن و بوتهٔ وسط جاده، به‌ویژه در قاب خودنگری، حذف شوند. برای نشان‌دادن پیوستگی، اشیای اضافی اختراع نشوند. جزئیات بیشتر اگر منطق تصویر را خراب کنند، باید کم شوند. حذف این اشیا مختص این داستان است و ممنوعیت جهانی در کتاب نیست.
- صورتی فقط در قاب اول حضور دارد؛ در قاب دوم و سوم، حتی در پس‌زمینه، نباشد. این خواسته مختص همین تصویر است.
- جهت نگاه دو مرحله کاملاً متفاوت باشد: در قاب اول صورت زرد به سمت کفشِ صورتی می‌چرخد و همان کفش هدف توجه است؛ فقط در قاب دوم به کفش‌های خودش نگاه می‌کند. صرف نوشتن جملهٔ مربوط به دیگری بالای سر، جهت نگاه غلط را اصلاح نمی‌کند. این تفاوت باید از چرخش چهره و کنش بدن خوانده شود.
- اگر زرد در قاب اول به کفشی اشاره می‌کند، همان کفشِ صورتی باید بند باز داشته باشد، نه کفش بستهٔ دیگر. کاربر اشاره‌کردن را الزامی نکرده است؛ حالت طبیعی دست‌های دونده نیز مجاز است، به شرط وضوح جهت نگاه.
- بررسی اجراییِ عامل برای تحقق بند باز: روی کفشِ باز، گره و دو حلقهٔ پاپیونِ بسته باقی نماند؛ دو سر آزاد کوتاه از روی کفش دیده شوند. این کنترل شامل کفش جلوی صورتی، هر دو کفش زرد در دو قاب اول و کفش آزاد زرد در قاب سوم است. فقط کفش زیر دست در قاب بستن می‌تواند حلقه‌ای در حال ساخته‌شدن داشته باشد؛ کفش عقب صورتی بسته است.
- فقط یکی از کفش‌های صورتی بند باز دارد. بندهای باز باید دو رشتهٔ کوتاهِ طبیعی باشند که از سوراخ‌های بالای روی کفش بیرون آمده و مطابق جاذبه افتاده‌اند؛ رشتهٔ بلند و شناور از پاشنه، کف کفش یا پشت پا ممنوع است. زرد در قاب دوم هر دو بند باز خودش را می‌بیند و در قاب سوم با لبخند می‌بندد.
- نسخهٔ اصلاح‌شده منتظر بررسی است؛ درخواست ویرایش یا نزدیک‌بودن سبک، تأیید نهایی یا اجازهٔ دانلود خودکارِ آن نسخه نیست.
