from rest_framework import serializers
from Prescreener.models import ProjectGroupPrescreener
from Surveyentry.models import *
from django.db.models import F
# from employee.models import EmployeeProfile

questiondict = {"ab" :	"Аҳаҧсуақәа азы бызшәа ҳәҧышәа","aa" :	"Enter Your Date of Birth","af" :	"Gee jou geboortedatum","ak" :	"Hyehyɛ Da a Wowoo Wo","sq" :	"Shkruani datën tuaj të lindjes","am" :	"የልደት ቀንዎን ያስገቡ","ar" :	"أدخل تاريخ ميلادك","an" :	"Entra a tuya Data de Naximiento","hy" :	"Մուտքագրեք Ձեր ծննդյան ամսաթիվը","as" :	"আপোনাৰ জন্ম তাৰিখ লিখক","av" :	"Хьоме дата нуцбурт кхьатай","ae" :	"Enter Your Date of Birth","ay" :	"Kuna urus yurïta uk qillqt’asim","az" :	"Doğum Tarixinizi daxil edin","bm" :	"I ka wolodon sɛbɛn","ba" :	"Цитата килтереү индексы ағымдағы йылдаң тәүге кварталы","eu" :	"Enter Your Date of Birth","be" :	"Увядзіце дату нараджэння","bn" :	"আপনার জন্মতারিখ প্রদান করুন","bh" :	"Enter Your Date of Birth","bi" :	"Sekaem nom blong yu i stap wea?","bs" :	"Unesite Vaš datum rođenja","br" :	"Kemm e vo ho darempred mat ?","bg" :	"Въведете датата си на раждане","my" :	"သင်၏မွေးသက္ကရာဇ်ကိုထည့်ပါ။","ca" :	"Introdueix la teva data de neixament","ch" :	"Iniri iyo' gi dato-mu.","ce" :	"Веда берча байнийни дӀаяхь булдату доб бошу.","ny" :	"Lowetsani Tsiku Lanu Lobadwa","zh" :	"输入你的出生日期","cv" :	"Тӗрӗмӗн пур кун","kw" :	"Entrewgh agas dedhyans a veu bredhek","co" :	"Inserite a vostra data di nascita","cr" :	"ᓇᔅᑎᒥᐸᒥᒄ ᒥᔅᑭᒥᐦᑖᕐᒧᑯᐣ","hr" :	"Unesite svoj datum rođenja","cs" :	"Zadejte své datum narození","da" :	"Indtast din fødselsdato","dv" :	"އުފަންދުވަސް ލިޔެލާށެވެ","nl" :	"Vul je geboortedatum in","dz" :	"ངའི་གནས་ཚེས་གྲངས་ཀློག་སྐར་མང་བཅས་འབྲེལ་ཡོད་པའི་ཚེས་གྲངས་བཟུང་འབྲེལ་བཞུགས།","en" :	"Enter Your Date of Birth","eo" :	"Enigu Vian Daton de Naskiĝo","et" :	"Sisesta oma sünnikuupäev","ee" :	"Ŋlɔ Wò Dzigbezã","fo" :	"Legg inn føðingardagin tín","fj" :	"Tukuna na Nomu Sigataka ni Rogoca","fi" :	"Anna syntymäaikasi","fr" :	"Entrez votre date de naissance","ff" :	"Mo Di Mi Do Fr Sa Do Fr Sa Do Fr Sa","gl" :	"Introduza a súa data de nacemento","ka" :	"Შეიყვანეთ თქვენი დაბადების თარიღი","de" :	"Gib dein Geburtsdatum ein","el" :	"Εισάγετε την ημερομηνία γέννησής σας","gn" :	"Emoinge Nde Ára Reñói hague","gu" :	"તમારી જન્મ તારીખ દાખલ કરો","ht" :	"Antre Dat Nesans Ou","ha" :	"Shigar da Ranar Haihuwar ku","he" :	"הכנס תאריך לידה","hz" :	"Gaa-huuru datera yoohepo yoo wuende.","hi" :	"आपका जन्म तारीख प्रवेश करे","ho" :	"Raitim yu yet long yu bi o birth.","hu" :	"Írja be a születési dátumát","ia" :	"Enter Your Date of Birth","id" :	"Masukkan tanggal lahir Anda","ie" :	"Entre vostre date de naissance.","ga" :	"Cuir isteach Do Dáta Breithe","ig" :	"Tinye ụbọchị ọmụmụ gị","ik" :	"Iñuŋŋauniaġaaq Date of Birth-a.","io" :	"Entrez vua dato di nasko","is" :	"Sláðu inn fæðingardag þinn","it" :	"Inserisci la tua data di nascita","iu" :	"ᐱᓇᓱᒥᐊᕐᖅ ᐃᓄᒃᑎᑐᑦ ᑐᒥᖅᑯᑦ","ja" :	"生年月日を入力","jv" :	"Ketik Tanggal Lair","kl" :	"Ukiuni pillugu avatangiassuseqassat","kn" :	"ನಿಮ್ಮ ಜನ್ಮ ದಿನಾಂಕವನ್ನು ನಮೂದಿಸಿ","kr" :	"Shiga kowane ranar zuciya mu.","ks" :	"تھویں تہٗر تورو تاریخ زندگی ییتھ زور کرو","kk" :	"Туған күніңізді енгізіңіз","km" :	"បញ្ចូល​ថ្ងៃ​កំណើត​របស់​អ្នក","ki" :	"Ingia Nguo Ya Thayo cia Kuhiga","rw" :	"Injira Itariki Yavutse","ky" :	"Туулган күнүңүздү киргизиңиз","kv" :	"Enter Your Date of Birth","kg" :	"Enter Your Date of Birth","ko" :	"생년월일을 입력하세요","ku" :	"Dîroka Jidayikbûna xwe binivîse","kj" :	"Enter Your Date of Birth","la" :	"Intra tuum Dies Natus","lb" :	"Gitt Äre Gebuertsdatum un","lg" :	"Enter Your Date of Birth","li" :	"Geej dien Geboortedatum in","ln" :	"Tyá Mokolo ya Mbotama na Yo","lo" :	"ໃສ່ວັນເດືອນປີເກີດຂອງເຈົ້າ","lt" :	"Įveskite savo gimimo datą","lu" :	"Tanga Tshisumbulu tsha wewe wa Kuseba","lv" :	"Ievadiet savu dzimšanas datumu","gv" :	"Enter Your Date of Birth","mk" :	"Внеси го твојот датум на раѓање","mg" :	"Ampidiro ny daty nahaterahanao","ms" :	"Masukkan tarikh lahir anda","ml" :	"നിങ്ങളുടെ ജനനത്തീയതി നൽകുക","mt" :	"Daħħal id-Data tat-Twelid Tiegħek","mi" :	"Whakauruhia to Ra whanau","mr" :	"तुमची जन्मतारीख टाका","mh" :	"Enter Your Date of Birth","mn" :	"Төрсөн огноогоо оруулна уу","na" :	"Daonim aōri ieta ereta ko non.","nv" :	"Hózhǫ́ǫ́gi áhééh nááhaazlání daaztsaastsoh dóó yádaałtsoh binitsʼáádah.","nd" :	"Dlala Isikhathi Sakho Sokuzalwa.","ne" :	"आफ्नो जन्म मिति प्रविष्ट गर्नुहोस्","ng" :	"Ombidi dO tuva yO ongepo?","nb" :	"Skriv inn fødselsdatoen din","nn" :	"Skriv inn din fødselsdato","no" :	"Skriv inn fødselsdatoen din","ii" :	"Enter Your Date of Birth","nr" :	"Enter Your Date of Birth","oc" :	"Introduire sa data de naissença","oj" :	"Gaawiinendaawaa niigaan e-niizhwaaswi dibaajimowin.","om" :	"Guyyaa Dhaloota Keessan Galchaa","cu" :	"Въведите дату рождения своего","to" :	"Fakatupu 'o e 'aho 'o e fakapule'anga 'o e hou'eiki 'o ha'u ki he loto.","or" :	"ଆପଣଙ୍କର ଜନ୍ମ ତାରିଖ ପ୍ରବେଶ କରନ୍ତୁ |","os" :	"Артын азырын ирдӕнты донты рӕйынд стандын.","pa" :	"ਆਪਣੀ ਜਨਮ ਮਿਤੀ ਦਾਖਲ ਕਰੋ","pi" :	"ඔබගේ උපන්දිනය ඇතුළත් කරන්න","fa" :	"تاریخ تولد خود را وارد کنید","pl" :	"Podaj swoją datę urodzenia","ps" :	"خپل د زیږون نیټه دننه کړئ","pt" :	"Digite sua data de nascimento","qu" :	"Nacesqayki punchawta qillqay","rm" :	"Deditg la data da naissance","rn" :	"Injiza itariki yawe y'amavuko.","ro" :	"Introduceți data nașterii","ru" :	"Введите вашу дату рождения","sa" :	"जन्मतिथिं प्रविशतु","sc" :	"Inserisci sa data de su nàschimentu tuo","sd" :	"پنھنجي پيدائش جي تاريخ داخل ڪريو","se" :	"Čuoŋomuitalit duinna bargu","sm" :	"Ulufale lou Aso Fanau","sg" :	"Ngbalaga na yo ya kobandela","sr" :	"Унесите свој датум рођења","gd" :	"Enter Your Date of Birth","sn" :	"Isa Zuva Rako Rekuzvarwa","si" :	"ඔබගේ උපන් දිනය ඇතුලත් කරන්න","sk" :	"Zadajte dátum narodenia","sl" :	"Vnesite vaš datum rojstva","so" :	"Geli Taariikhda Dhalashadaada","st" :	"Kenya Letsatsi la Hao la Tsoalo","es" :	"Introduzca su fecha de nacimiento","su" :	"Lebetkeun Tanggal Lahir Anjeun","sw" :	"Weka Tarehe Yako ya Kuzaliwa","ss" :	"Ngena ngemvume nge-Data","sv" :	"Ange ditt födelsedatum","te" :	"మీ పుట్టిన తేదీని నమోదు చేయండి","tg" :	"Санаи таваллуди худро ворид кунед","th" :	"ใส่วันเกิดของคุณ","ti" :	"ዕለት ልደትካ ኣእቱ","bo" :	"ཁྱེད་རང་སྐར་བཅུ་ཐོག་རིག་གིས་ཕྱི་ལོ་གསར་བསྐྱོད།","tk" :	"Doglan senäňizi giriziň","tl" :	"Ilagay ang Iyong Petsa ng Kapanganakan","tn" :	"O nama","tr" :	"Doğum tarihinizi girin","ts" :	"Famba u nga dyondza mune wa wena wa ku tala.","tt" :	"Туган көнегезне кертегез","tw" :	"Yɛfrɛ wo Awọnabɔmu Sɛwo mu","ty" :	"Enter Your Date of Birth","ug" :	"تۇغۇلغان ۋاقتىڭىزنى كىرگۈزۈڭ","uk" :	"Введіть свою дату народження","ur" :	"اپنی تاریخ پیدائش درج کریں۔","uz" :	"Tug'ilgan kuningizni kiriting","ve" :	"Swika kha u ya ha vhukuma ya wena ya vhutshilo.","vi" :	"Nhập ngày sinh của bạn","wa" :	"Dëggal leen naat bu ñaari yoon.","cy" :	"Nodwch Eich Dyddiad Geni","wo" :	"Lees meer » Dood Date","fy" :	"Fier dyn bertedatum yn","xh" :	"Faka Umhla Wakho Wokuzalwa","yi" :	"אַרייַן דיין געבורט טאָג","yo" :	"Tẹ Ọjọ ibi rẹ sii","za" :	"Gyoengh Bouzc Laengh Gyoenz Nyiedz.","zu" :	"Faka Usuku Lwakho Lokuzalwa","ta" :	"உங்கள் பிறந்த தேதியை உள்ளிடவும்","vo" :	"Vödölöfobölövölölövölövölövölövölövölönövölövölö: Binomötobölövölövölövölövölövölövö","nld" :	"Enter Your Date of Birth","doi" :	"Enter Your Date of Birth","kok" :	"Enter Your Date of Birth","mai" :	"Enter Your Date of Birth","mni" :	"Enter Your Date of Birth","ori" :	"Enter Your Date of Birth","sat" :	"Enter Your Date of Birth","sot" :	"Kenya Letsatsi la Hao la Tsoalo","chn" :	"Enter Your Date of Birth","yue" :	"Enter Your Date of Birth","ph" :	"Enter Your Date of Birth","ct" :	"Enter Your Date of Birth"}

class RespondentSerializer(serializers.ModelSerializer):

    class Meta:
        model = RespondentDetail
        fields = '__all__'



class ProjectGroupPrescreenerTranslatedAnswersSerializer(serializers.ModelSerializer):

    exclusive = serializers.BooleanField(source='parent_answer.exclusive')

    class Meta:
        model = TranslatedAnswer
        fields = [
            'id', 'translated_answer','exclusive'
            ]



class ProjectGroupPrescreenerTranslatedQuestionsSerializer(serializers.ModelSerializer):

    all_responses = serializers.SerializerMethodField()

    def get_all_responses(self,obj):
        if self.context['client_code'] == 'toluna':
            answer_list = TranslatedAnswer.objects.filter(
                translated_parent_question = obj).exclude(toluna_answer_id__in = ['',None]).values(
                    'id', 'translated_answer','internal_answer_id',exclusive = F('parent_answer__exclusive'))
        elif self.context['client_code'] == 'zamplia':
            answer_list = TranslatedAnswer.objects.filter(
                translated_parent_question = obj).exclude(zamplia_answer_id__in = ['',None]).values(
                    'id', 'translated_answer','internal_answer_id',exclusive = F('parent_answer__exclusive'))
        else:
            answer_list = TranslatedAnswer.objects.filter(
                translated_parent_question = obj).values(
                    'id', 'translated_answer','internal_answer_id',exclusive = F('parent_answer__exclusive'))
        return answer_list

    class Meta:
        model = TranslatedQuestion
        fields = ['all_responses']


class ProjectGroupPrescreenerQuestionsListSerializer(serializers.ModelSerializer):

    translated_question_text = serializers.SerializerMethodField()
    parent_question_text = serializers.SerializerMethodField()
    parent_question_type = serializers.SerializerMethodField()
    parent_question_category = serializers.CharField(source='translated_question_id.parent_question.parent_question_category.category')
    Internalquestionnumber = serializers.CharField(source='translated_question_id.Internal_question_id')
    responses_from_question = serializers.SerializerMethodField()
    
    def get_responses_from_question(self, instance):
        return ProjectGroupPrescreenerTranslatedQuestionsSerializer(instance=instance.translated_question_id, context=self.context).data


    class Meta:
        model = ProjectGroupPrescreener
        fields = [
            'id', 'translated_question_id', 'sequence','translated_question_text','parent_question_text', 'parent_question_type', 'parent_question_category','responses_from_question','Internalquestionnumber']
    

    def get_translated_question_text(self,obj):
        if obj.translated_question_id.parent_question.parent_question_number in  ['Age','1001538','T1001538'] or obj.translated_question_id.parent_question.parent_question_type == 'NU':
            obj.translated_question_id.translated_question_text = questiondict[obj.project_group_id.project_group_language.language_code]
            return obj.translated_question_id.translated_question_text
        else:
            return obj.translated_question_id.translated_question_text

    def get_parent_question_text(self,obj):
        if obj.translated_question_id.parent_question.parent_question_number in  ['Age','1001538','T1001538'] or obj.translated_question_id.parent_question.parent_question_type == 'NU':
            obj.translated_question_id.parent_question.parent_question_text = questiondict[obj.project_group_id.project_group_language.language_code]
            return obj.translated_question_id.parent_question.parent_question_text
        else:
            return obj.translated_question_id.parent_question.parent_question_text
        
    def get_parent_question_type(self,obj):
        if obj.translated_question_id.parent_question.parent_question_number in  ['Age','1001538','T1001538'] or obj.translated_question_id.parent_question.parent_question_type == 'NU':
            obj.translated_question_id.parent_question.parent_question_type = "DT"
            return obj.translated_question_id.parent_question.parent_question_type
        else:
            return obj.translated_question_id.parent_question.parent_question_type


class PrescreenerForBeforeSurveyEntry(serializers.ModelSerializer):


    Internalquestionnumber = serializers.CharField(source='translated_question_id.Internal_question_id')
    all_answers = serializers.SerializerMethodField()
    allowed_answer_options = serializers.SerializerMethodField()
    
    def get_all_answers(self,obj):
        return (TranslatedAnswer.objects.filter(internal_question_id = obj.translated_question_id.Internal_question_id).values_list('internal_answer_id',flat=True))

    def get_allowed_answer_options(self,obj):
        return list(obj.allowedoptions.values_list('internal_answer_id',flat=True))


    class Meta:
        model = ProjectGroupPrescreener
        fields = ['Internalquestionnumber','all_answers', 'allowed_answer_options']
    