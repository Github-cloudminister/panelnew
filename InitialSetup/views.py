import json,requests,concurrent.futures
from knox.auth import TokenAuthentication
from rest_framework import permissions
from rest_framework.views import APIView
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group
from rest_framework.response import Response
from rest_framework import status
from ClientSupplierAPIIntegration.TolunaClientAPI.models import ClientDBCountryLanguageMapping
from Customer.models import ClientContact, Currency, CustomerOrganization
from Project.models import Language
from Questions.models import ParentAnswer, ParentQuestion, QuestionCategory, TranslatedAnswer, TranslatedQuestion, ZipCodeMappingTable
from Supplier.models import DisqoAPIPricing
from SupplierAPI.models import LucidCountryLanguageMapping
from Surveyentry.models import SurveyEntryWelcomePageContent
from employee.models import Country, EmployeeProfile
from django.conf import settings


max_workers = 10 if settings.SERVER_TYPE == 'localhost' else 50 


class InitialSetupView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        if settings.SERVER_TYPE == 'localhost':
            permission_obj = Permission.objects.all()
            model_name_list = ['employeeprofile', 'clientcontact', 'customerorganization', 'currency', 'country', 'language', 'project',
                                'suppliercontact', 'supplierorganisation']
            group_name_list = ['Create_Update_Employee', 'Create_Update_Client_Contact', 'Create_Update_Customer', 'Create_Update_Currency',
                                'Create_Update_Country', 'Create_Update_Language', 'Create_Update_Project_ProjectGroup_ProjectGroupSupplier',
                                'Create_Update_Supplier_Contact','Create_Update_Supplier']
            exist_permissions = []
            ch = 0
            for group_name in group_name_list:
                try:
                    # ************** Check Group Name *********************
                    group_obj = Group.objects.get(name = group_name)
                    exist_permissions.append(group_name)
                    pass
                except:
                    # ************** Create a Group with Name *********************
                    group_obj = Group(name = group_name)
                    group_obj.save()
                    
                    if model_name_list[ch] == "employeeprofile":
                        group_permissions = permission_obj.filter(content_type__model__in=[model_name_list[ch],"group","permission"])
                    elif model_name_list[ch] == "project":
                        group_permissions = permission_obj.filter(content_type__model__in=[model_name_list[ch],"projectgroup","projectgroupsupplier"])
                    else:
                        group_permissions = permission_obj.filter(content_type__model=model_name_list[ch])
                
                    # ************** Add Permission to the Group *********************
                    for group_perm in group_permissions:
                        group_obj.permissions.add(group_perm)
                        group_obj.save()
                    ch += 1


            country_list = {"A2": "Andorra Test", "AD": "Andorra", "AE": "United Arab Emirates", "AF": "Afghanistan", "AG": "Antigua and Barbuda", "AI": "Anguilla", "AL": "Albania", "AM": "Armenia", "AN": "Netherlands Antilles", "AO": "Angola", "AQ": "Antarctica", "AR": "Argentina", "AS": "American Samoa", "AT": "Austria", "AU": "Australia", "AW": "Aruba", "AZ": "Azerbaijan", "BA": "Bosnia and Herzegovina", "BB": "Barbados", "BD": "Bangladesh", "BE": "Belgium", "BF": "Burkina Faso", "BG": "Bulgaria", "BH": "Bahrain", "BI": "Burundi", "BJ": "Benin", "BL": "Saint BarthÃƒÂ©lemy", "BM": "Bermuda", "BN": "Brunei", "BO": "Bolivia", "BQ": "British Antarctic Territory", "BR": "Brazil", "BS": "Bahamas", "BT": "Bhutan", "BV": "Bouvet Island", "BW": "Botswana", "BY": "Belarus", "BZ": "Belize", "CA": "Canada", "CC": "Cocos [Keeling] Islands", "CD": "Congo - Kinshasa", "CF": "Central African Republic", "CG": "Congo - Brazzaville", "CH": "Switzerland", "CI": "Cote DIvoire", "CK": "Cook Islands", "CL": "Chile", "CM": "Cameroon", "CN": "China", "CO": "Colombia", "CR": "Costa Rica", "CS": "Serbia and Montenegro", "CT": "Canton and Enderbury Islands", "CU": "Cuba", "CV": "Cape Verde", "CX": "Christmas Island", "CY": "Cyprus", "CZ": "Czech Republic", "DD": "East Germany", "DE": "Germany", "DJ": "Djibouti", "DK": "Denmark", "DM": "Dominica", "DO": "Dominican Republic", "DZ": "Algeria", "EC": "Ecuador", "EE": "Estonia", "EG": "Egypt", "EH": "Western Sahara", "ER": "Eritrea", "ES": "Spain", "ET": "Ethiopia", "FI": "Finland", "FJ": "Fiji", "FK": "Falkland Islands", "FM": "Micronesia", "FO": "Faroe Islands", "FQ": "French Southern and Antarctic Territories", "FR": "France", "FX": "Metropolitan France", "GA": "Gabon", "GB": "United Kingdom", "GD": "Grenada", "GE": "Georgia", "GF": "French Guiana", "GG": "Guernsey", "GH": "Ghana", "GI": "Gibraltar", "GL": "Greenland", "GM": "Gambia", "GN": "Guinea", "GP": "Guadeloupe", "GQ": "Equatorial Guinea", "GR": "Greece", "GS": "South Georgia and the South Sandwich Islands", "GT": "Guatemala", "GU": "Guam", "GW": "Guinea-Bissau", "GY": "Guyana", "HK": "Hong Kong SAR China", "HM": "Heard Island and McDonald Islands", "HN": "Honduras", "HR": "Croatia", "HT": "Haiti", "HU": "Hungary", "ID": "Indonesia", "IE": "Ireland", "IL": "Israel", "IM": "Isle of Man", "IN": "India", "IO": "British Indian Ocean Territory", "IQ": "Iraq", "IR": "Iran", "IS": "Iceland", "IT": "Italy", "JE": "Jersey", "JM": "Jamaica", "JO": "Jordan", "JP": "Japan", "JT": "Johnston Island", "KE": "Kenya", "KG": "Kyrgyzstan", "KH": "Cambodia", "KI": "Kiribati", "KM": "Comoros", "KN": "Saint Kitts and Nevis", "KP": "North Korea", "KR": "South Korea", "KW": "Kuwait", "KY": "Cayman Islands", "KZ": "Kazakhstan", "LA": "Laos", "LB": "Lebanon", "LC": "Saint Lucia", "LI": "Liechtenstein", "LK": "Sri Lanka", "LR": "Liberia", "LS": "Lesotho", "LT": "Lithuania", "LU": "Luxembourg", "LV": "Latvia", "LY": "Libya", "MA": "Morocco", "MC": "Monaco", "MD": "Moldova", "ME": "Montenegro", "MF": "Saint Martin", "MG": "Madagascar", "MH": "Marshall Islands", "MI": "Midway Islands", "MK": "Macedonia", "ML": "Mali", "MM": "Myanmar [Burma]", "MN": "Mongolia", "MO": "Macau SAR China", "MP": "Northern Mariana Islands", "MQ": "Martinique", "MR": "Mauritania", "MS": "Montserrat", "MT": "Malta", "MU": "Mauritius", "MV": "Maldives", "MW": "Malawi", "MX": "Mexico", "MY": "Malaysia", "MZ": "Mozambique", "NA": "Namibia", "NC": "New Caledonia", "NE": "Niger", "NF": "Norfolk Island", "NG": "Nigeria", "NI": "Nicaragua", "NL": "Netherlands", "NO": "Norway", "NP": "Nepal", "NQ": "Dronning Maud Land", "NR": "Nauru", "NT": "Neutral Zone", "NU": "Niue", "NZ": "New Zealand", "OM": "Oman", "PA": "Panama", "PC": "Pacific Islands Trust Territory", "PE": "Peru", "PF": "French Polynesia", "PG": "Papua New Guinea", "PH": "Philippines", "PK": "Pakistan", "PL": "Poland", "PM": "Saint Pierre and Miquelon", "PN": "Pitcairn Islands", "PR": "Puerto Rico", "PS": "Palestinian Territories", "PT": "Portugal", "PU": "U.S. Miscellaneous Pacific Islands", "PW": "Palau", "PY": "Paraguay", "PZ": "Panama Canal Zone", "QA": "Qatar", "RE": "Reunion", "RO": "Romania", "RS": "Serbia", "RU": "Russia", "RW": "Rwanda", "SA": "Saudi Arabia", "SB": "Solomon Islands", "SC": "Seychelles", "SD": "Sudan", "SE": "Sweden", "SG": "Singapore", "SH": "Saint Helena", "SI": "Slovenia", "SJ": "Svalbard and Jan Mayen", "SK": "Slovakia", "SL": "Sierra Leone", "SM": "San Marino", "SN": "Senegal", "SO": "Somalia", "SR": "Suriname", "ST": "Sao Tome and Principe", "SU": "Union of Soviet Socialist Republics", "SV": "El Salvador", "SY": "Syria", "SZ": "Swaziland", "TC": "Turks and Caicos Islands", "TD": "Chad", "TF": "French Southern Territories", "TG": "Togo", "TH": "Thailand", "TJ": "Tajikistan", "TK": "Tokelau", "TL": "Timor-Leste", "TM": "Turkmenistan", "TN": "Tunisia", "TO": "Tonga", "TR": "Turkey", "TT": "Trinidad and Tobago", "TV": "Tuvalu", "TW": "Taiwan", "TZ": "Tanzania", "UA": "Ukraine", "UG": "Uganda", "UM": "U.S. Minor Outlying Islands", "US": "United States", "UY": "Uruguay", "UZ": "Uzbekistan", "VA": "Vatican City", "VC": "Saint Vincent and the Grenadines", "VD": "North Vietnam", "VE": "Venezuela", "VG": "British Virgin Islands", "VI": "U.S. Virgin Islands", "VN": "Vietnam", "VU": "Vanuatu", "WF": "Wallis and Futuna", "WK": "Wake Island", "WS": "Samoa", "YD": "People's Democratic Republic of Yemen", "YE": "Yemen", "YT": "Mayotte", "ZA": "South Africa", "ZM": "Zambia", "ZW": "Zimbabwe", "ZZ": "Unknown or Invalid Region"}
            exist_country = {}
            for c in country_list:
                try:
                    country_obj = Country.objects.get(country_code = c)
                    exist_country[c] = country_list[c]
                except:
                    country_obj = Country(country_code = c, country_name = country_list[c])
                    country_obj.save()
            
            theorem_country_id_list = {"A2": None, "AD": None, "AE": "44db6c3f-34bf-4682-b7c7-bf336e7d687b", "AF": None, "AG": None, "AI": None, "AL": None, "AM": None, "AN": None, "AO": None, "AQ": None, "AR": "1bb42394-b037-49c6-9053-5b326c62dee2", "AS": None, "AT": None, "AU": "6683bb57-1e3b-449e-8879-a2bfeaf29844", "AW": None, "AZ": None, "BA": None, "BB": None, "BD": None, "BE": "e5b59a23-7250-444b-963c-872ab6483e5e", "BF": None, "BG": "fbcd0c81-8e77-4537-b7d9-36e449329f3e", "BH": None, "BI": None, "BJ": None, "BL": None, "BM": None, "BN": None, "BO": None, "BQ": None, "BR": "d57657f9-a942-4841-b2b5-c533a6f123bc", "BS": None, "BT": None, "BV": None, "BW": None, "BY": None, "BZ": None, "CA": "6779df3c-289b-4f9e-9cdc-32186239525f", "CC": None, "CD": None, "CF": None, "CG": None, "CH": "ec566eb2-32fa-412e-b0c1-62f7e4544867", "CI": None, "CK": None, "CL": None, "CM": None, "CN": "98f187de-54c4-4091-ba56-8581a1c6fac1", "CO": "67778224-fb77-46c2-829f-27ab7e8d57da", "CR": None, "CS": None, "CT": None, "CU": None, "CV": None, "CX": None, "CY": None, "CZ": "fb9ab421-6269-46b2-9387-a45fcbcafbfa", "DD": None, "DE": "1400fc59-1cfa-4698-bee6-f5d686b639e2", "DJ": None, "DK": "6851455f-1dd0-4263-b33a-e2fe0d0bcdd9", "DM": None, "DO": None, "DZ": None, "EC": None, "EE": None, "EG": "e5899f4a-709d-4681-8b5e-03e7e9dfad02", "EH": None, "ER": None, "ES": "f7cf25bc-2bcb-4d7f-a827-02427f93ec7b", "ET": None, "FI": "8380b4e8-ce96-457b-84c8-65b780e52083", "FJ": None, "FK": None, "FM": None, "FO": None, "FQ": None, "FR": "d5944158-7205-4fa9-8622-23246476cf3e", "FX": None, "GA": None, "GB": "9ecdb05d-284d-43f0-aaab-a84e18458cd1", "GD": None, "GE": None, "GF": None, "GG": None, "GH": None, "GI": None, "GL": None, "GM": None, "GN": None, "GP": None, "GQ": None, "GR": "e738f110-98cc-4435-8fd5-9d7c4b7d0346", "GS": None, "GT": None, "GU": None, "GW": None, "GY": None, "HK": "566ee0ce-a52a-4bdb-ad9e-63028aea123a", "HM": None, "HN": None, "HR": None, "HT": None, "HU": "860a85f0-4fc0-4d78-84ae-0cd4c814332a", "ID": "1277fba4-e0d0-4a48-9d30-14ce0833c517", "IE": "22881fef-fb99-423c-b403-15e40c7a3230", "IL": None, "IM": None, "IN": "7084f90b-55b1-4a94-9f3e-e87ef5fe02f7", "IO": None, "IQ": None, "IR": None, "IS": None, "IT": "98487696-b4d6-49a1-8197-18dbbe535908", "JE": None, "JM": None, "JO": None, "JP": "79428a81-c69e-4c53-969d-3b47906f1b0d", "JT": None, "KE": None, "KG": None, "KH": None, "KI": None, "KM": None, "KN": None, "KP": None, "KR": "3cfa985d-fe6d-4cb9-9930-ed5e9cfa1272", "KW": "8dd354d4-11bc-49bd-9ee2-64b52812776f", "KY": None, "KZ": None, "LA": None, "LB": None, "LC": None, "LI": None, "LK": None, "LR": None, "LS": None, "LT": "6b610dfd-bb71-4409-9550-063f04e7e3f3", "LU": None, "LV": None, "LY": None, "MA": None, "MC": None, "MD": None, "ME": None, "MF": None, "MG": None, "MH": None, "MI": None, "MK": None, "ML": None, "MM": None, "MN": None, "MO": None, "MP": None, "MQ": None, "MR": None, "MS": None, "MT": None, "MU": None, "MV": None, "MW": None, "MX": "372da156-a7aa-4900-a69a-5eb975623139", "MY": "cc43da5a-04f6-4ff7-9308-eb18ee791514", "MZ": None, "NA": None, "NC": None, "NE": None, "NF": None, "NG": None, "NI": None, "NL": "e8919ef5-1bb3-407c-ad56-76200f242391", "NO": "529a3b54-d7d6-4bab-962c-f0c54dc227d5", "NP": None, "NQ": None, "NR": None, "NT": None, "NU": None, "NZ": "3fdeda19-8c15-4119-9d82-9843b3861824", "OM": "4f4d2695-6606-4400-bd4b-a9f7a7138b9f", "PA": None, "PC": None, "PE": "6a7a4767-4eae-442d-b3d5-07eef2eecf07", "PF": None, "PG": None, "PH": "ae432fbf-8f92-4adf-963f-05f34d22bbd5", "PK": None, "PL": "5bcdc2ec-d233-48fd-8561-a48992f90cf5", "PM": None, "PN": None, "PR": None, "PS": None, "PT": "0866c735-0fda-4340-ac12-ff25ce3dcb9a", "PU": None, "PW": None, "PY": None, "PZ": None, "QA": "6a8766da-c177-464d-8b37-033d5d1a79b3", "RE": None, "RO": "6ed81b53-fed5-4687-8b74-c5e613bef398", "RS": None, "RU": "f8523b10-5e47-472d-9b97-ded436dc5e87", "RW": None, "SA": "73d08355-747c-477e-945e-852082089259", "SB": None, "SC": None, "SD": None, "SE": "16c98c27-0b20-4005-a6a5-9e099066397d", "SG": "70c53d75-e388-4142-ae43-726ee5c96f43", "SH": None, "SI": None, "SJ": None, "SK": None, "SL": None, "SM": None, "SN": None, "SO": None, "SR": None, "ST": None, "SU": None, "SV": None, "SY": None, "SZ": None, "TC": None, "TD": None, "TF": None, "TG": None, "TH": "63f585cf-7c96-49b9-bbae-56087c713cd4", "TJ": None, "TK": None, "TL": None, "TM": None, "TN": None, "TO": None, "TR": "55edd4a5-6906-4402-b4a3-2fe836fcf688", "TT": None, "TV": None, "TW": "39ed5069-6159-403c-bbe1-8f14ecaf1152", "TZ": None, "UA": "ad43376d-ff55-4106-9684-ced3ed5c145b", "UG": None, "UM": None, "US": "5a8296a0-0ab0-4e75-be00-71a6371b519b", "UY": "eea37397-ff32-4a73-88b7-0e86689cb79d", "UZ": None, "VA": None, "VC": None, "VD": None, "VE": None, "VG": None, "VI": None, "VN": "caa55fbe-7ce2-49e2-a561-615b978d768c", "VU": None, "WF": None, "WK": None, "WS": None, "YD": None, "YE": None, "YT": None, "ZA": "5e579ffa-bb54-47e8-b19d-440de0994d28", "ZM": None, "ZW": None, "ZZ": None}

            for theorem_country_code in theorem_country_id_list:
                try:
                    country_obj = Country.objects.get(country_code = theorem_country_code)
                    country_obj.theorem_country_id = theorem_country_id_list[theorem_country_code]
                    country_obj.save(force_update=True)
                except:
                    pass

            language_list = {"ab" : "Abkhazian",  "aa" : "Afar",  "af" : "Afrikaans",  "ak" : "Akan",  "sq" : "Albanian",  "am" : "Amharic",  "ar" : "Arabic",  "an" : "Aragonese",  "hy" : "Armenian",  "as" : "Assamese",  "av" : "Avaric",  "ae" : "Avestan",  "ay" : "Aymara",  "az" : "Azerbaijani",  "bm" : "Bambara",  "ba" : "Bashkir",  "eu" : "Basque",  "be" : "Belarusian",  "bn" : "Bengali",  "bh" : "Biharilanguages",  "bi" : "Bislama",  "bs" : "Bosnian",  "br" : "Breton",  "bg" : "Bulgarian",  "my" : "Burmese",  "ca" : "Catalanm",  "ch" : "Chamorro",  "ce" : "Chechen",  "ny" : "Chichewa",  "zh" : "Chinese",  "cv" : "Chuvash",  "kw" : "Cornish",  "co" : "Corsican",  "cr" : "Cree",  "hr" : "Croatian",  "cs" : "Czech",  "da" : "Danish",  "dv" : "Divehi",  "nl" : "Dutch",  "dz" : "Dzongkha",  "en" : "English",  "eo" : "Esperanto",  "et" : "Estonian",  "ee" : "Ewe",  "fo" : "Faroese",  "fj" : "Fijian",  "fi" : "Finnish",  "fr" : "French",  "ff" : "Fulah",  "gl" : "Galician",  "ka" : "Georgian",  "de" : "German",  "el" : "Greek",  "gn" : "Guarani",  "gu" : "Gujarati",  "ht" : "Haitian",  "ha" : "Hausa",  "he" : "Hebrew",  "hz" : "Herero",  "hi" : "Hindi",  "ho" : "HiriMotu",  "hu" : "Hungarian",  "ia" : "Interlingua",  "id" : "Indonesian",  "ie" : "Interlingue",  "ga" : "Irish",  "ig" : "Igbo",  "ik" : "Inupiaq",  "io" : "Ido",  "is" : "Icelandic",  "it" : "Italian",  "iu" : "Inuktitut",  "ja" : "Japanese",  "jv" : "Javanese",  "kl" : "Kalaallisut",  "kn" : "Kannada",  "kr" : "Kanuri",  "ks" : "Kashmiri",  "kk" : "Kazakh",  "km" : "CentralKhmer",  "ki" : "Kikuyu",  "rw" : "Kinyarwanda",  "ky" : "Kirghiz",  "kv" : "Komi",  "kg" : "Kongo",  "ko" : "Korean",  "ku" : "Kurdish",  "kj" : "Kuanyama",  "la" : "Latin",  "lb" : "Luxembourgish",  "lg" : "Ganda",  "li" : "Limburgan",  "ln" : "Lingala",  "lo" : "Lao",  "lt" : "Lithuanian",  "lu" : "Luba-Katanga",  "lv" : "Latvian",  "gv" : "Manx",  "mk" : "Macedonian",  "mg" : "Malagasy",  "ms" : "Malay",  "ml" : "Malayalam",  "mt" : "Maltese",  "mi" : "Maori",  "mr" : "Marathi",  "mh" : "Marshallese",  "mn" : "Mongolian",  "na" : "Nauru",  "nv" : "Navajo",  "nd" : "NorthNdebele",  "ne" : "Nepali",  "ng" : "Ndonga",  "nb" : "Norwegian Bokmal",  "nn" : "Norwegian Nynorsk",  "no" : "Norwegian",  "ii" : "SichuanYi",  "nr" : "South Ndebele",  "oc" : "Occitan",  "oj" : "Ojibwa",  "om" : "Oromo",  "cu" : "ChurchÂ Slavic",  "to" : "TongaÂ (TongaIslands)",  "or" : "Oriya",  "os" : "Ossetian",  "pa" : "Punjabi",  "pi" : "Pali",  "fa" : "Persian",  "pl" : "Polish",  "ps" : "Pashto",  "pt" : "Portuguese",  "qu" : "Quechua",  "rm" : "Romansh",  "rn" : "Rundi",  "ro" : "Romanian",  "ru" : "Russian",  "sa" : "Sanskrit",  "sc" : "Sardinian",  "sd" : "Sindhi",  "se" : "NorthernSami",  "sm" : "Samoan",  "sg" : "Sango",  "sr" : "Serbian",  "gd" : "Gaelic",  "sn" : "Shona",  "si" : "Sinhala",  "sk" : "Slovak",  "sl" : "Slovenian",  "so" : "Somali",  "st" : "SouthernSotho",  "es" : "Spanish",  "su" : "Sundanese",  "sw" : "Swahili",  "ss" : "Swati",  "sv" : "Swedish",  "te" : "Telugu",  "tg" : "Tajik",  "th" : "Thai",  "ti" : "Tigrinya",  "bo" : "Tibetan",  "tk" : "Turkmen",  "tl" : "Tagalog",  "tn" : "Tswana",  "tr" : "Turkish",  "ts" : "Tsonga",  "tt" : "Tatar",  "tw" : "Twi",  "ty" : "Tahitian",  "ug" : "Uighur",  "uk" : "Ukrainian",  "ur" : "Urdu",  "uz" : "Uzbek",  "ve" : "Venda",  "vi" : "Vietnamese",  "wa" : "Walloon",  "cy" : "Welsh",  "wo" : "Wolof",  "fy" : "WesternFrisian",  "xh" : "Xhosa",  "yi" : "Yiddish",  "yo" : "Yoruba",  "za" : "Zhuang",  "zu" : "Zulu",  "ta" : "Tamil",  "vo" : "VolapÃ¼k", "nld":"Flemish", "doi":"Dogri", "kok":"Konkani", "mai":"Maithili", "mni":"Manipuri", "ori":"Odia", "sat":"Santali", "sot":"Sesotho", "chn":"Chinese Simplified", "yue":"Cantonese", "ph":"Filipino", "ct":"Traditional Chinese"}
            exist_language = {}
            page_content = {'ab': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'aa': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'af': ['Dankie dat u ingestem het om deel te neem aan ons opname. ', 'U opinies is vir ons belangrik. Verskaf vriendelike en bedagsame antwoorde vir elke vraag om u deelname te laat tel. ', 'U antwoorde sal vertroulik gehou word en slegs in totaal gebruik word. ', 'Klik Volgende om voort te gaan! ', 'Volgende '], 'ak': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sq': ['Faleminderit që ranë dakord për të marrë pjesë në sondazhin tonë. ', 'Opinionet tuaja janë të rëndësishme për ne, me mirësi jepni përgjigje të ndershme dhe të zhytura në mendime për secilën pyetje, në mënyrë që pjesëmarrja juaj të vlejë. ', 'Përgjigjet tuaja do të mbahen konfidenciale dhe do të përdoren vetëm në total. ', 'Ju lutemi Klikoni Next për të Vazhduar! ', 'Tjetra '], 'am': ['በእኛ የዳሰሳ ጥናት ለመሳተፍ ስለተስማሙ እናመሰግናለን። ', 'የእርስዎ አስተያየት ለእኛ አስፈላጊ ነው ፣ የእራስዎ ተሳትፎ ቆጠራ ለማድረግ ለእያንዳንዱ ጥያቄ ሐቀኛ እና አሳቢ ምላሾችን በደግነት ያቅርቡ ፡፡ ', 'የእርስዎ ምላሾች በሚስጥር ይቀመጣሉ እና በጥቅሉ ብቻ ጥቅም ላይ ይውላሉ። ', 'ለመቀጠል እባክዎን ቀጣዩን ጠቅ ያድርጉ! ', 'ቀጣይ '], 'ar': ['شكرا لموافقتك على المشاركة في الاستبيان الخاص بنا. ', 'آرائك مهمة بالنسبة لنا ، يرجى تقديم إجابات صادقة ومدروسة لكل سؤال من أجل جعل مشاركتك مهمة. ', 'سيتم الاحتفاظ بسرية ردودك وسيتم استخدامها بشكل إجمالي فقط. ', 'الرجاء النقر فوق "التالي" للمتابعة! ', 'التالى '], 'an': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'hy': ['Շնորհակալություն մեր հարցմանը մասնակցելու համաձայնության համար: ', 'Ձեր կարծիքները մեզ համար կարևոր են, յուրաքանչյուր հարցի համար բարյացակամորեն տրամադրեք ազնիվ և մտածված պատասխաններ ՝ ձեր մասնակցությունը հաշվարկելու համար: ', 'Ձեր պատասխանները կպահպանվեն գաղտնի և կօգտագործվեն միայն համախառն: ', 'Շարունակելու համար սեղմեք Հաջորդը: ', 'Հաջորդը '], 'as': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'av': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ae': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ay': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'az': ['Anketimizdə iştirak etməyi qəbul etdiyiniz üçün təşəkkür edirik. ', 'Fikirləriniz bizim üçün vacibdir, iştirak sayılmasını təmin etmək üçün hər sual üçün dürüst və düşünülmüş cavablar verin. ', 'Cavablarınız məxfi saxlanacaq və yalnız ümumilikdə istifadə olunacaq. ', 'Zəhmət olmasa davam etmək üçün Next düyməsini vurun! ', 'Növbəti '], 'bm': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ba': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'eu': ['Eskerrik asko gure inkestan parte hartzearekin ados egoteagatik. ', 'Zure iritziak garrantzitsuak dira guretzat; mesedez, erantzun bakoitzari erantzun zintzoak eta zorrotzak eman, zure parte hartzea zenbatekoa izan dadin. ', 'Zure erantzunak isilpean gordeko dira eta agregatuan soilik erabiliko dira. ', 'Mesedez, sakatu Hurrengoa Jarraitzeko! ', 'Hurrengoa '], 'be': ['Дзякуем Вам за згоду прыняць удзел у нашым апытанні. ', 'Вашы меркаванні важныя для нас, калі ласка, дайце сумленныя і ўдумлівыя адказы на кожнае пытанне, каб ваш улік быў важным. ', 'Вашы адказы будуць канфідэнцыяльнымі і будуць выкарыстоўвацца толькі ў сукупнасці. ', 'Націсніце "Далей", каб працягнуць! ', 'Далей '], 'bn': ['আমাদের সমীক্ষায় অংশ নিতে সম্মত হওয়ার জন্য আপনাকে ধন্যবাদ। ', 'আপনার মতামত আমাদের কাছে গুরুত্বপূর্ণ, আপনার অংশগ্রহণকে গণনা করার জন্য দয়া করে প্রতিটি প্রশ্নের জন্য সৎ ও চিন্তাশীল প্রতিক্রিয়া সরবরাহ করুন। ', 'আপনার প্রতিক্রিয়াগুলি গোপনীয় রাখা হবে এবং কেবলমাত্র সামগ্রিকভাবে ব্যবহৃত হবে। ', 'অবিরত করতে পরবর্তী ক্লিক করুন! ', 'পরবর্তী '], 'bh': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'bi': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'bs': ['Zahvaljujemo što ste pristali da učestvujete u našoj anketi. ', 'Vaša mišljenja su nam važna, pružite iskrene i promišljene odgovore na svako pitanje kako bi vaše sudjelovanje bilo važno. ', 'Vaši će odgovori biti povjerljivi i upotrebljavat će se samo u zbirnom obliku. ', 'Kliknite Dalje za nastavak! ', 'Sljedeći '], 'br': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'bg': ['Благодарим Ви, че се съгласихте да участвате в нашето проучване. ', 'Вашите мнения са важни за нас, любезно дайте честни и обмислени отговори за всеки въпрос, за да накарате вашето участие да се брои. ', 'Вашите отговори ще се пазят в тайна и ще се използват само обобщено. ', 'Моля, щракнете Напред, за да продължите! ', 'Следващия '], 'my': ['ကျွန်ုပ်တို့၏စစ်တမ်းတွင်ပါဝင်ရန်သဘောတူခြင်းအတွက်ကျေးဇူးတင်ပါသည်။ ', 'သင်၏ထင်မြင်ချက်များသည်ကျွန်ုပ်တို့အတွက်အရေးကြီးသည်။ သင်၏ပါဝင်မှုကိုရေတွက်နိုင်ရန်အတွက်မေးခွန်းတစ်ခုစီအတွက်ရိုးသား။ စဉ်းစားဟန်ရှိသောတုံ့ပြန်မှုများကိုကြင်နာစွာပေးပါ။ ', 'သင်၏တုံ့ပြန်မှုများကိုလျှို့ဝှက်ထားမည်ဖြစ်ပြီးစုစုပေါင်းတွင်သာအသုံးပြုလိမ့်မည်။ ', 'ဆက်လက်ဆောင်ရွက်ရန် Next ကိုနှိပ်ပါ! ', 'နောက်တစ်ခု '], 'ca': ['Gràcies per acceptar participar en la nostra enquesta. ', 'Les vostres opinions són importants per a nosaltres; amablement proporcioneu respostes honestes i reflexives per a cada pregunta per tal que la vostra participació compti. ', 'Les vostres respostes es mantindran confidencials i només s’utilitzaran de forma agregada. ', 'Feu clic a Següent per continuar. ', 'Pròxim '], 'ch': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ce': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ny': ['Zikomo chifukwa chovomera kutenga nawo mbali pa kafukufuku wathu. ', 'Malingaliro anu ndiofunikira kwa ife, mokoma mtima perekani mayankho achilungamo komanso oganiza pafunso lililonse kuti mutenge nawo mbali. ', 'Mayankho anu azisungidwa mwachinsinsi ndipo adzagwiritsidwa ntchito limodzi. ', 'Chonde Dinani Kenako kuti Mupitirize! ', 'Ena '], 'zh': ['感谢您同意参加我们的调查。 ', '您的意见对我们很重要，请为每个问题提供诚实，周到的回答，以使您的参与度很高。 ', '您的回复将被保密，仅用于汇总。 ', '请单击下一步继续！ ', '下一个 '], 'cv': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'kw': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'co': ['Grazie per Accettà di Participà à u nostru sondaggio. ', 'E vostre opinioni sò impurtanti per noi, furnite gentilmente risposte oneste è riflessive per ogni dumanda per fà cuntà a vostra participazione. ', 'E vostre risposte seranu mantenute cunfidenziali è seranu aduprate solu in aggregatu. ', 'Per piacè Cliccate Seguente per Cuntinuà! ', 'Dopu '], 'cr': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'hr': ['Zahvaljujemo što ste pristali sudjelovati u našoj anketi. ', 'Vaša su nam mišljenja važna, pružite iskrene i promišljene odgovore na svako pitanje kako bi vaše sudjelovanje bilo važno. ', 'Vaši će odgovori biti povjerljivi i upotrebljavat će se samo u cjelini. ', 'Kliknite Dalje za nastavak! ', 'Sljedeći '], 'cs': ['Děkujeme za souhlas s účastí v našem průzkumu. ', 'Vaše názory jsou pro nás důležité, poskytněte laskavé a promyšlené odpovědi na každou otázku, aby se vaše účast mohla počítat. ', 'Vaše odpovědi budou utajeny a budou použity pouze souhrnně. ', 'Pokračujte kliknutím na Další! ', 'další '], 'da': ['Tak fordi du accepterer at deltage i vores undersøgelse. ', 'Dine meninger er vigtige for os, vær venlig at give ærlige og tankevækkende svar på hvert spørgsmål for at få din deltagelse til at tælle. ', 'Dine svar bliver fortroligt og vil kun blive brugt samlet. ', 'Klik på Næste for at fortsætte! ', 'Næste '], 'dv': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'nl': ['Bedankt voor uw toestemming om deel te nemen aan onze enquête. ', 'Uw mening is belangrijk voor ons, geef op elke vraag eerlijke en doordachte antwoorden om ervoor te zorgen dat uw deelname telt. ', 'Uw reacties zullen vertrouwelijk worden behandeld en zullen alleen in geaggregeerde vorm worden gebruikt. ', 'Klik op Volgende om door te gaan! ', 'De volgende '], 'dz': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'en': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'eo': ['Dankon Por Konsenti Partopreni Nian Enketon. ', 'Viaj opinioj gravas por ni, bonvolu doni honestajn kaj pripensajn respondojn por ĉiu demando por ke via partopreno kalkulu. ', 'Viaj respondoj restos konfidencaj kaj estos uzataj entute. ', 'Bonvolu Klaki Sekva por Daŭrigi! ', 'Poste '], 'et': ['Täname, et nõustute meie uuringus osalema. ', 'Teie arvamused on meie jaoks olulised, pakkuge iga küsimuse jaoks ausaid ja läbimõeldud vastuseid, et teie osalemine loeks. ', 'Teie vastuseid hoitakse konfidentsiaalsetena ja neid kasutatakse ainult kokkuvõtlikult. ', 'Palun jätkamiseks klõpsake nuppu Edasi! ', 'Järgmine '], 'ee': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'fo': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'fj': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'fi': ['Kiitos suostumuksestasi osallistua kyselymme. ', 'Mielipiteesi ovat meille tärkeitä, antakaa ystävällisesti rehelliset ja harkitut vastaukset jokaiseen kysymykseen, jotta saatte osallistumistanne tärkeän. ', 'Vastauksesi pidetään luottamuksellisina, ja niitä käytetään vain yhteenvetona. ', 'Napsauta Seuraava jatkaaksesi! ', 'Seuraava '], 'fr': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ff': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'gl': ['Grazas por aceptar participar na nosa enquisa. ', 'As túas opinións son importantes para nós. Por favor, contesta respostas honestas e atentas para cada pregunta para que a túa participación conte. ', 'As túas respostas manteranse confidenciais e só se usarán de forma agregada. ', 'Por favor, faga clic en Seguinte para continuar. ', 'A continuación '], 'ka': ['მადლობას გიხდით, რომ ეთანხმებით ჩვენს კვლევაში მონაწილეობას. ', 'თქვენი მოსაზრებები ჩვენთვის მნიშვნელოვანია. გთხოვთ, თითოეულ კითხვაზე მოგვაწოდოთ გულწრფელი და გააზრებული პასუხი, რათა თქვენი მონაწილეობა იყოს გათვლილი. ', 'თქვენი პასუხები დაცული იქნება კონფიდენციალური და გამოყენებული იქნება მხოლოდ ჯამურად. ', 'გასაგრძელებლად დააჭირეთ შემდეგს! ', 'შემდეგი '], 'de': ['Vielen Dank für Ihre Zustimmung zur Teilnahme an unserer Umfrage. ', 'Ihre Meinungen sind uns wichtig. Geben Sie bitte ehrliche und nachdenkliche Antworten auf jede Frage, damit Ihre Teilnahme zählt. ', 'Ihre Antworten werden vertraulich behandelt und nur in ihrer Gesamtheit verwendet. ', 'Bitte klicken Sie auf Weiter, um fortzufahren! ', 'Nächster '], 'el': ['Σας ευχαριστούμε που συμφωνήσατε να συμμετάσχετε στην έρευνά μας. ', 'Οι απόψεις σας είναι σημαντικές για εμάς, παρακαλούμε να δώσετε ειλικρινείς και στοχαστικές απαντήσεις για κάθε ερώτηση προκειμένου να μετρήσετε τη συμμετοχή σας. ', 'Οι απαντήσεις σας θα παραμείνουν εμπιστευτικές και θα χρησιμοποιηθούν μόνο συνολικά. ', 'Κάντε κλικ στο Επόμενο για να συνεχίσετε! ', 'Επόμενο '], 'gn': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'gu': ['અમારા સર્વેમાં ભાગ લેવા સંમતિ આપવા બદલ આભાર. ', 'તમારા મંતવ્યો અમારા માટે મહત્વપૂર્ણ છે, તમારી ભાગીદારીની ગણતરી કરવા માટે દરેક પ્રશ્નના માયાળુ પ્રમાણિક અને વિચારશીલ જવાબો પ્રદાન કરો. ', 'તમારા જવાબો ગુપ્ત રાખવામાં આવશે અને ફક્ત એકંદરમાં ઉપયોગમાં લેવામાં આવશે. ', 'કૃપા કરીને ચાલુ રાખવા માટે આગળ ક્લિક કરો! ', 'આગળ '], 'ht': ['Mèsi pou Dakò Patisipe nan sondaj nou an. ', 'Opinyon ou yo enpòtan pou nou, tanpri bay repons onèt ak reflechi pou chak kesyon yo nan lòd yo fè patisipasyon ou konte. ', 'Repons ou yo ap kenbe konfidansyèl epi yo pral itilize an total sèlman. ', 'Tanpri klike sou Next pou kontinye! ', 'Next '], 'ha': ['Na Gode da Amincewa Domin Shiga Cikin bincikenmu. ', "Ra'ayoyinku suna da mahimmanci a gare mu, ta hanyar bayar da amsoshi masu gaskiya da tunani don kowane tambaya don sanya ƙimar ku ta ƙidaya. ", "Amsoshinku zasu zama na sirri kuma za'a yi amfani dasu a cikin tara kawai. ", 'Da fatan za a Danna Next don Ci gaba! ', 'Na gaba '], 'he': ['תודה שהסכמת להשתתף בסקר שלנו. ', 'חוות הדעת שלך חשובות לנו, ספק בחביבות תשובות כנות ומחושבות על כל שאלה בכדי לגרום להשתתפות שלך לספור. ', 'התגובות שלך יישמרו בסודיות וישמשו באופן מצטבר בלבד. ', 'אנא לחץ על הבא כדי להמשיך! ', 'הַבָּא '], 'hz': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'hi': ['हमारे सर्वेक्षण में भाग लेने के लिए सहमत होने के लिए धन्यवाद। ', 'आपकी राय हमारे लिए महत्वपूर्ण है, कृपया अपनी भागीदारी की गिनती करने के लिए प्रत्येक प्रश्न के लिए ईमानदार और विचारशील प्रतिक्रियाएं प्रदान करें। ', 'आपकी प्रतिक्रियाओं को गोपनीय रखा जाएगा और केवल समुच्चय में उपयोग किया जाएगा। ', 'जारी रखने के लिए कृपया अगला क्लिक करें! ', 'आगे '], 'ho': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'hu': ['Köszönjük, hogy vállalta, hogy részt vesz felmérésünkben. ', 'Véleménye fontos számunkra, minden kérdésre adjon őszinte és átgondolt válaszokat annak érdekében, hogy a részvétele számít. ', 'Válaszait bizalmasan kezeljük, és csak összesítve használjuk fel. ', 'Kérjük, kattintson a Tovább gombra a folytatáshoz! ', 'Következő '], 'ia': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'id': ['Terima kasih telah setuju untuk berpartisipasi dalam survei kami. ', 'Pendapat Anda penting bagi kami, berikan tanggapan yang jujur dan bijaksana untuk setiap pertanyaan agar partisipasi Anda berarti. ', 'Tanggapan Anda akan dijaga kerahasiaannya dan hanya akan digunakan secara agregat. ', 'Silakan Klik Berikutnya untuk Melanjutkan! ', 'Lanjut '], 'ie': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ga': ['Go raibh maith agat as Aontú Páirt a ghlacadh inár Suirbhé. ', 'Tá do chuid tuairimí tábhachtach dúinn, tabhair freagraí macánta macánta ar gach ceist d’fhonn do rannpháirtíocht a chomhaireamh. ', 'Coinneofar do chuid freagraí faoi rún agus úsáidfear iad ina n-iomláine. ', 'Cliceáil Ar Aghaidh le do thoil Lean! ', 'Ar Aghaidh '], 'ig': ['Daalụ maka ikwere isonye na nyocha anyị. ', 'Echiche gị dị anyị mkpa, jiri nwayọ nye azịza eziokwu na ezi uche maka ajụjụ ọ bụla iji mee ka nsonye gị gụọ. ', 'Nzaghachi gị ga-abụ ihe nzuzo ma jiri ya na nchịkọta naanị. ', "Biko Pịa Next na-aga n'ihu! ", 'Osote '], 'ik': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'io': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'is': ['Þakka þér fyrir að samþykkja að taka þátt í könnuninni okkar. ', 'Skoðanir þínar eru okkur mikilvægar, vinsamlegast gefðu heiðarleg og hugsi svör við hverri spurningu til að láta þátttöku þína telja. ', 'Svörum þínum verður haldið trúnaðarmálum og verða aðeins notuð samanlagt. ', 'Vinsamlegast smelltu á Næsta til að halda áfram! ', 'Næst '], 'it': ['Grazie per aver accettato di partecipare al nostro sondaggio. ', 'Le tue opinioni sono importanti per noi, fornisci gentilmente risposte oneste e ponderate per ogni domanda in modo che la tua partecipazione conti. ', 'Le tue risposte saranno mantenute riservate e verranno utilizzate solo in forma aggregata. ', 'Fare clic su Avanti per continuare! ', 'Il prossimo '], 'iu': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ja': ['調査への参加に同意していただきありがとうございます。 ', 'あなたの意見は私たちにとって重要であり、あなたの参加を重要視するために、各質問に対して正直で思慮深い回答を提供してください。 ', 'あなたの回答は秘密にされ、集合的にのみ使用されます。 ', '[次へ]をクリックして続行してください。 ', '次 '], 'jv': ['Matur Nuwun Wis Setuju Melu Survei. ', 'Pendapat sampeyan penting kanggo kita, wenehi tanggapan sing jujur lan migunani kanggo saben pitakon supaya partisipasi sampeyan dietung. ', 'Tanggepan sampeyan bakal tetep rahasia lan bakal digunakake kanthi agregat. ', 'Mangga Klik Sabanjure kanggo Terusake! ', 'Sabanjure '], 'kl': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'kn': ['ನಮ್ಮ ಸಮೀಕ್ಷೆಯಲ್ಲಿ ಭಾಗವಹಿಸಲು ಒಪ್ಪಿದ್ದಕ್ಕಾಗಿ ಧನ್ಯವಾದಗಳು. ', 'ನಿಮ್ಮ ಅಭಿಪ್ರಾಯಗಳು ನಮಗೆ ಮುಖ್ಯ, ನಿಮ್ಮ ಭಾಗವಹಿಸುವಿಕೆಯನ್ನು ಎಣಿಸುವಂತೆ ಪ್ರತಿ ಪ್ರಶ್ನೆಗೆ ಪ್ರಾಮಾಣಿಕವಾಗಿ ಮತ್ತು ಚಿಂತನಶೀಲ ಪ್ರತಿಕ್ರಿಯೆಗಳನ್ನು ದಯೆಯಿಂದ ಒದಗಿಸಿ. ', 'ನಿಮ್ಮ ಪ್ರತಿಕ್ರಿಯೆಗಳನ್ನು ಗೌಪ್ಯವಾಗಿಡಲಾಗುತ್ತದೆ ಮತ್ತು ಒಟ್ಟಾರೆಯಾಗಿ ಮಾತ್ರ ಬಳಸಲಾಗುತ್ತದೆ. ', 'ಮುಂದುವರಿಸಲು ದಯವಿಟ್ಟು ಮುಂದೆ ಕ್ಲಿಕ್ ಮಾಡಿ! ', 'ಮುಂದೆ '], 'kr': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ks': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'kk': ['Біздің сауалнамаға қатысуға келіскеніңіз үшін рахмет. ', 'Сіздің пікірлеріңіз біз үшін маңызды, сіздің қатысуыңызды санау үшін әр сұраққа шынайы және мұқият жауап беріңіз. ', 'Сіздің жауаптарыңыз құпия сақталады және тек жиынтықта қолданылады. ', 'Жалғастыру үшін Келесі түймесін басыңыз! ', 'Келесі '], 'km': ['សូមអរគុណចំពោះការយល់ព្រមក្នុងការចូលរួមក្នុងការស្ទង់មតិរបស់យើង។ ', 'យោបល់របស់អ្នកមានសារៈសំខាន់ចំពោះយើងផ្តល់ការឆ្លើយតបដោយស្មោះត្រង់និងគិតគូរសម្រាប់សំណួរនីមួយៗដើម្បីធ្វើឱ្យការចូលរួមរបស់អ្នករាប់។ ', 'ការឆ្លើយតបរបស់អ្នកនឹងត្រូវរក្សាជាការសម្ងាត់ហើយនឹងត្រូវប្រើជារួម។ ', 'សូមចុចបន្ទាប់ដើម្បីបន្ត! ', 'បន្ទាប់ '], 'ki': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'rw': ['Urakoze Kwemera Kugira uruhare Mubushakashatsi Bwacu. ', 'Ibitekerezo byawe ni ingenzi kuri twe, ubigiranye umutima mwiza utange ibisubizo byukuri kandi utekereje kuri buri kibazo kugirango ubone uruhare rwawe. ', 'Ibisubizo byawe bizabikwa ibanga kandi bizakoreshwa muri rusange. ', 'Nyamuneka Kanda ahakurikira kugirango ukomeze! ', 'Ibikurikira '], 'ky': ['Биздин сурамжылоого катышууга макул болгонуңуз үчүн рахмат. ', 'Сиздин пикириңиз биз үчүн маанилүү, сиздин катышууңузду эске алуу үчүн ар бир суроого чынчыл жана терең ойлонуп жооп бериңиз. ', 'Сиздин жоопторуңуз купуя сакталат жана жалпысынан гана колдонулат. ', 'Улантуу үчүн Кийинкини чыкылдатыңыз! ', 'Кийинки '], 'kv': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'kg': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ko': ['설문 조사 참여에 동의 해 주셔서 감사합니다. ', '귀하의 의견은 우리에게 중요하며 귀하의 참여를 중요하게 생각할 수 있도록 각 질문에 대해 정직하고 사려 깊은 답변을 제공합니다. ', '귀하의 답변은 기밀로 유지되며 총체적으로 만 사용됩니다. ', '계속하려면 다음을 클릭하십시오! ', '다음 '], 'ku': ['Spas Ji Bo Ku Hûn Bibe Beşdarê Anketa Me. ', 'Ramanên we ji me re girîng in, ji kerema xwe ji bo her pirsê bersivên dilsoz û ramîner bidin da ku beşdarbûna we jimartin. ', 'Bersivên we dê nehênî werin hiştin û dê bi tenê bi tevahî werin bikar anîn. ', 'Ji kerema xwe Vê Bikirtînin da ku Berdewam bikin! ', 'Piştî '], 'kj': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'la': ['Tibi gratias ago tibi quoniam Favens interesse nostra Survey . ', 'Sententias referre nobis benigne providere singulis responsa quaestione pia cogitatione ad tuam summam participationem . ', 'Respondeo non posse custodiri secretum tua et tantum in complexu . ', 'Next Click to Perge quaeso ! ', 'deinde '], 'lb': ['Merci fir averstanen un eiser Ëmfro deelzehuelen. ', 'Är Meenunge si wichteg fir eis, liwwert éierlech an nodenklech Äntwerte fir all Fro fir Är Participatioun zielen ze loossen. ', 'Är Äntwerte gi vertraulech gehalen a ginn nëmmen ugesammelt benotzt. ', 'Klickt w.e.g. nächst fir weiderzemaachen! ', 'Nächst '], 'lg': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'li': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ln': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'lo': ['ຂອບໃຈ ສຳ ລັບການຕົກລົງທີ່ຈະເຂົ້າຮ່ວມໃນການ ສຳ ຫຼວດຂອງພວກເຮົາ. ', 'ຄວາມຄິດເຫັນຂອງທ່ານມີຄວາມ ສຳ ຄັນຕໍ່ພວກເຮົາ, ໃຫ້ ຄຳ ຕອບທີ່ຈິງໃຈແລະມີຄວາມຄິດ ສຳ ລັບແຕ່ລະ ຄຳ ຖາມເພື່ອໃຫ້ການເຂົ້າຮ່ວມຂອງທ່ານນັບໄດ້. ', 'ຄຳ ຕອບຂອງທ່ານຈະຖືກຮັກສາໄວ້ເປັນຄວາມລັບແລະຈະຖືກ ນຳ ໃຊ້ໂດຍລວມເທົ່ານັ້ນ. ', 'ກະລຸນາກົດ Next ເພື່ອສືບຕໍ່! ', 'ຕໍ່ໄປ '], 'lt': ['Ačiū, kad sutikote dalyvauti mūsų apklausoje. ', 'Jūsų nuomonė mums svarbi, maloniai atsakykite į kiekvieną klausimą sąžiningai ir apgalvotai, kad jūsų dalyvavimas būtų svarbus. ', 'Jūsų atsakymai bus konfidencialūs ir bus naudojami tik kartu. ', 'Spustelėkite Pirmyn, jei norite tęsti! ', 'Kitas '], 'lu': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'lv': ['Paldies, ka piekritāt piedalīties mūsu aptaujā. ', 'Jūsu viedoklis mums ir svarīgs. Lūdzu, sniedziet godīgas un pārdomātas atbildes uz katru jautājumu, lai jūsu dalība būtu svarīga. ', 'Jūsu atbildes tiks uzskatītas par konfidenciālām, un tās tiks izmantotas tikai kopumā. ', 'Lūdzu, noklikšķiniet uz Tālāk, lai turpinātu! ', 'Nākamais '], 'gv': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'mk': ['Ви благодариме што се согласивте да учествувате во нашето истражување. ', 'Вашите мислења се важни за нас, provideубезно дајте искрени и внимателни одговори на секое прашање со цел да го направите вашето учество брое. ', 'Вашите одговори ќе бидат чувани во доверливост и ќе се користат само збирно. ', 'Ве молиме, кликнете Следно за да продолжите! ', 'Следно '], 'mg': ["Misaotra anao nanaiky handray anjara amin'ny fanadihadianay. ", 'Zava-dehibe aminay ny hevitrao, manomeza am-pitiavana ireo valiny marina sy feno fiheverana isaky ny fanontaniana mba hampandeha ny anjara birikinao. ', "Ho tsiambaratelo ny valinteninao ary hampiasaina amin'ny fampiangonana fotsiny. ", 'Azafady tsindrio ny manaraka mba hanohizana! ', 'Manaraka '], 'ms': ['Terima kasih kerana bersetuju untuk mengambil bahagian dalam tinjauan kami. ', 'Pendapat anda penting bagi kami, sila berikan jawapan yang jujur dan bijaksana untuk setiap soalan untuk membuat penyertaan anda dihitung. ', 'Respons anda akan dirahsiakan dan hanya akan digunakan secara agregat. ', 'Sila Klik Seterusnya untuk Terus! ', 'Seterusnya '], 'ml': ['ഞങ്ങളുടെ സർവേയിൽ പങ്കെടുക്കാൻ സമ്മതിച്ചതിന് നന്ദി. ', 'നിങ്ങളുടെ അഭിപ്രായങ്ങൾ ഞങ്ങൾക്ക് പ്രധാനമാണ്, നിങ്ങളുടെ പങ്കാളിത്തം കണക്കാക്കുന്നതിന് ഓരോ ചോദ്യത്തിനും സത്യസന്ധവും ചിന്താപരവുമായ പ്രതികരണങ്ങൾ നൽകുക. ', 'നിങ്ങളുടെ പ്രതികരണങ്ങൾ രഹസ്യാത്മകമായി സൂക്ഷിക്കുകയും മൊത്തത്തിൽ മാത്രം ഉപയോഗിക്കുകയും ചെയ്യും. ', 'തുടരുന്നതിന് ദയവായി അടുത്തത് ക്ലിക്കുചെയ്യുക! ', 'അടുത്തത് '], 'mt': ['Grazzi talli qbilt li tipparteċipa fl-istħarriġ tagħna. ', 'L-opinjonijiet tiegħek huma importanti għalina, ġentilment ipprovdi tweġibiet onesti u maħsubin għal kull mistoqsija sabiex il-parteċipazzjoni tiegħek tgħodd. ', 'It-tweġibiet tiegħek se jinżammu kunfidenzjali u se jintużaw biss flimkien. ', 'Jekk jogħġbok Ikklikkja Li jmiss biex Tkompli! ', 'Li jmiss '], 'mi': ['Mauruuru No Te Whakaae Ki Te Whakauru Mai Ki Te Whakauru Mai Ki Te Whakauru Atu Ki Te Tono Ki To Tatou Ruri. ', 'He mea nui o whakaaro ki a maatau, ma te atawhai e whakarato nga whakautu pono me te whai whakaaro mo ia paatai kia tatau ai to whakauru. ', 'Ka noho muna pea o whakautu, ka whakamahia noa iho. ', 'Tena Paatohia a Panuku kia Tonu! ', 'Panuku '], 'mr': ['आमच्या सर्वेक्षणात भाग घेण्यासाठी सहमती दिल्याबद्दल धन्यवाद. ', 'आपली मते आमच्यासाठी महत्त्वपूर्ण आहेत, आपला सहभाग मोजण्यासाठी प्रत्येक प्रश्नासाठी दयाळूपणे प्रामाणिक आणि विचारशील प्रतिसाद द्या. ', 'आपले प्रतिसाद गोपनीय ठेवले जातील आणि केवळ एकूणच वापरले जातील. ', 'कृपया सुरू ठेवण्यासाठी पुढील क्लिक करा! ', 'पुढे '], 'mh': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'mn': ['Бидний санал асуулгад оролцохыг зөвшөөрсөнд баярлалаа. ', 'Таны санал бодол бидний хувьд чухал бөгөөд оролцоогоо тооцохын тулд асуулт тус бүрт үнэнч, няхуур байдлаар хариулаарай. ', 'Таны хариултыг нууцлах бөгөөд зөвхөн нэгтгэн ашиглах болно. ', 'Үргэлжлүүлэхийн тулд Дараа товшино уу! ', 'Дараачийн '], 'na': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'nv': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'nd': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ne': ['हाम्रो सर्वेक्षणमा भाग लिन सहमतिका लागि धन्यबाद। ', 'तपाईंको विचार हाम्रो लागि महत्त्वपूर्ण छ, कृपया तपाइँको सहभागिता गणना गर्न प्रत्येक प्रश्नको लागि इमान्दार र विचारशील प्रतिक्रियाहरू प्रदान गर्नुहोस्। ', 'तपाईंको प्रतिक्रियाहरू गोप्य राखिनेछ र समग्रमा मात्र प्रयोग गरिन्छ। ', 'कृपया जारी राख्नको लागि अर्को क्लिक गर्नुहोस्! ', 'अर्को '], 'ng': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'nb': ['Takk for at du gikk med på å delta i undersøkelsen vår. ', 'Dine meninger er viktige for oss, vennligst gi ærlige og gjennomtenkte svar på hvert spørsmål for å få din deltakelse til å telle. ', 'Svarene dine vil bli holdt konfidensielle og vil bare bli brukt samlet. ', 'Klikk Neste for å fortsette! ', 'Neste '], 'nn': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'no': ['Takk for at du gikk med på å delta i undersøkelsen vår. ', 'Dine meninger er viktige for oss, vennligst gi ærlige og gjennomtenkte svar på hvert spørsmål for å få din deltakelse til å telle. ', 'Svarene dine vil bli holdt konfidensielle og vil bare bli brukt samlet. ', 'Klikk Neste for å fortsette! ', 'Neste '], 'ii': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'nr': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'oc': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'oj': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'om': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'cu': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'to': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'or': ['ଆମର ସର୍ଭେରେ ଭାଗ ନେବାକୁ ରାଜି ହୋଇଥିବାରୁ ଧନ୍ୟବାଦ | ', 'ତୁମର ମତାମତ ଆମ ପାଇଁ ଗୁରୁତ୍ୱପୂର୍ଣ୍ଣ, ତୁମର ଅଂଶଗ୍ରହଣକୁ ଗଣନା କରିବା ପାଇଁ ଦୟାକରି ପ୍ରତ୍ୟେକ ପ୍ରଶ୍ନ ପାଇଁ ସଚ୍ଚୋଟ ଏବଂ ଚିନ୍ତିତ ପ୍ରତିକ୍ରିୟା ପ୍ରଦାନ କର | ', 'ତୁମର ପ୍ରତିକ୍ରିୟାଗୁଡ଼ିକୁ ଗୋପନୀୟ ରଖାଯିବ ଏବଂ କେବଳ ଏଗ୍ରିମେଣ୍ଟରେ ବ୍ୟବହୃତ ହେବ | ', 'ଜାରି ରଖିବାକୁ ଦୟାକରି ପରବର୍ତ୍ତୀ କ୍ଲିକ୍ କରନ୍ତୁ! ', 'ପରବର୍ତ୍ତୀ '], 'os': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'pa': ['ਸਾਡੇ ਸਰਵੇਖਣ ਵਿਚ ਹਿੱਸਾ ਲੈਣ ਲਈ ਸਹਿਮਤ ਹੋਣ ਲਈ ਤੁਹਾਡਾ ਧੰਨਵਾਦ. ', 'ਤੁਹਾਡੀਆਂ ਰਾਇਵਾਂ ਸਾਡੇ ਲਈ ਮਹੱਤਵਪੂਰਣ ਹਨ, ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੀ ਭਾਗੀਦਾਰੀ ਦੀ ਗਿਣਤੀ ਕਰਨ ਲਈ ਹਰ ਪ੍ਰਸ਼ਨ ਲਈ ਦਿਆਲੂ ਅਤੇ ਇਮਾਨਦਾਰ ਜਵਾਬ ਦਿਓ. ', 'ਤੁਹਾਡੇ ਜਵਾਬ ਗੁਪਤ ਰੱਖੇ ਜਾਣਗੇ ਅਤੇ ਸਿਰਫ ਸਮੁੱਚੇ ਰੂਪ ਵਿੱਚ ਵਰਤੇ ਜਾਣਗੇ. ', 'ਕਿਰਪਾ ਕਰਕੇ ਜਾਰੀ ਰੱਖਣ ਲਈ ਅੱਗੇ ਕਲਿੱਕ ਕਰੋ! ', 'ਅਗਲਾ '], 'pi': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'fa': ['از توافق شما برای شرکت در نظرسنجی ما متشکریم ', 'نظرات شما برای ما مهم است ، لطفاً برای هر س honestال پاسخ صادقانه و متفکرانه ای ارائه دهید تا مشارکت شما را حساب کند. ', 'پاسخ های شما محرمانه نگه داشته می شوند و فقط در مجموع استفاده می شوند. ', 'لطفا برای ادامه کلیک کنید بعدی! ', 'بعد '], 'pl': ['Dziękujemy za wyrażenie zgody na udział w naszej ankiecie. ', 'Twoje opinie są dla nas ważne, uprzejmie udziel uczciwych i przemyślanych odpowiedzi na każde pytanie, aby Twój udział się liczył. ', 'Twoje odpowiedzi będą traktowane jako poufne i zostaną wykorzystane tylko zbiorczo. ', 'Kliknij Dalej, aby kontynuować! ', 'Kolejny '], 'ps': ['زموږ په سروې کې برخه اخیستنې موافقې لپاره مننه. ', 'ستاسو نظرونه زموږ لپاره مهم دي ، په مهربانۍ سره د هرې پوښتنې لپاره صادق او فکري ځوابونه وړاندې کړئ ترڅو ستاسو د ګډون شمیره جوړه شي. ', 'ستاسو ځوابونه به محرم وساتل شي او یوازې په مجموع کې به وکارول شي. ', 'مهرباني وکړئ ادامه ورکولو لپاره کلیک وکړئ! ', 'بل '], 'pt': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'qu': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'rm': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'rn': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ro': ['Vă mulțumim că sunteți de acord să participați la sondajul nostru. ', 'Opiniile dvs. sunt importante pentru noi, oferim cu amabilitate răspunsuri oneste și atentă pentru fiecare întrebare, pentru a face participarea dvs. să conteze. ', 'Răspunsurile dvs. vor fi păstrate confidențiale și vor fi utilizate numai în totalitate. ', 'Vă rugăm să faceți clic pe Următorul pentru a continua! ', 'Următor → '], 'ru': ['Благодарим вас за согласие принять участие в нашем опросе. ', 'Ваше мнение важно для нас, просьба давать честные и вдумчивые ответы на каждый вопрос, чтобы ваше участие было засчитано. ', 'Ваши ответы останутся конфиденциальными и будут использоваться только в совокупности. ', 'Пожалуйста, нажмите «Далее», чтобы продолжить! ', 'следующий '], 'sa': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sc': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sd': ['اسان جي سروي ۾ حصو وٺڻ تي راضي ٿيڻ جي مهرباني. ', 'توهان جا رايا اسان لاءِ اهم آهن ، مهرباني ڪري توهان جي شرڪت کي ڳڻپ ڪرڻ لاءِ هر سوال لاءِ ايماندار ۽ سوچيندڙ جواب ڏيو. ', 'توهان جا جواب راز ۾ رکيا ويندا ۽ صرف مجموعي ۾ استعمال ڪيا ويندا. ', 'جاري رکڻ لاءِ اڳيان ڪلڪ ڪريو ', 'اڳتي '], 'se': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sm': ['Faafetai mo le malilie e auai i la matou suesuega. ', 'O ou manatu e taua ia matou, agalelei agalelei ma mafaufau loloto tali mo fesili taʻitasi ina ia mafai ai ona avea lou auai faitauga. ', 'O au tali o le a faʻalilolilo ma o le a faʻaaogaina i le naʻo le faʻaopoopoina. ', 'Faʻamolemole kiliki le isi e faʻaauau! ', 'Le isi '], 'sg': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sr': ['Хвала вам што сте пристали да учествујете у нашој анкети. ', 'Ваша мишљења су нам важна, пружите искрене и промишљене одговоре на свако питање како би ваше учешће било важно. ', 'Ваши одговори ће бити поверљиви и користиће се само збирно. ', 'Кликните на Нект да бисте наставили! ', 'Следећи '], 'gd': ['Tapadh leibh airson aontachadh pàirt a ghabhail san sgrùdadh againn. ', 'Tha na beachdan agad cudromach dhuinn, thoir dhuinn freagairtean onarach agus smaoineachail airson gach ceist gus am bi do chom-pàirteachadh a ’cunntadh. ', 'Thèid na freagairtean agad a chumail dìomhair agus thèid an cleachdadh gu h-iomlan a-mhàin. ', 'Feuch an cliog thu Next gus leantainn air adhart! ', 'An ath rud '], 'sn': ['Ndinokutendai Nekubvumirana Kutora Nhaurwa mune Yedu Ongororo. ', 'Maonero ako akakosha kwatiri, nemutsa tipe mhinduro dzakavimbika uye dzinofunga pamubvunzo wega wega kuitira kuti kutora chikamu kwako kuverengere. ', 'Mhinduro dzako dzichachengetwa zvakavanzika uye dzinozoshandiswa muhuwandu chete. ', 'Ndapota Dzvanya Next kuti Uenderere mberi ', 'Inotevera '], 'si': ['අපගේ සමීක්ෂණයට සහභාගී වීමට එකඟ වීම ගැන ස්තූතියි. ', 'ඔබගේ අදහස් අපට වැදගත් වන අතර, ඔබේ සහභාගීත්වය ගණනය කිරීම සඳහා සෑම ප්\u200dරශ්නයකටම අවංක හා කල්පනාකාරී ප්\u200dරතිචාර ලබා දෙන්න. ', 'ඔබගේ ප්\u200dරතිචාර රහසිගතව තබා ඇති අතර එය සමස්තයක් ලෙස පමණක් භාවිතා වේ. ', 'ඉදිරියට යාමට කරුණාකර ඊළඟ ක්ලික් කරන්න! ', 'ලබන '], 'sk': ['Ďakujeme, že ste sa dohodli na účasti v našom prieskume. ', 'Vaše názory sú pre nás dôležité. Prosíme, poskytnite čestné a premyslené odpovede na každú otázku, aby sa vaša účasť rátala. ', 'Vaše odpovede budú dôverné a budú použité iba súhrnne. ', 'Pokračujte kliknutím na Ďalej! ', 'Ďalšie '], 'sl': ['Zahvaljujemo se vam za soglasje za sodelovanje v naši anketi. ', 'Vaša mnenja so za nas pomembna, prisrčno in iskreno odgovorite na vsako vprašanje, da boste lahko sodelovali. ', 'Vaši odgovori bodo zaupni in bodo uporabljeni samo v celoti. ', 'Za nadaljevanje kliknite Naprej! ', 'Naslednji '], 'so': ['Waad ku mahadsantahay ogolaashaha inaad kaqaybqaadato sahankeena. ', "Fikradahaaga ayaa muhiim noo ah, si naxariis leh u bixi jawaabo daacad ah oo feker leh su'aal kasta si looga dhigo ka-qaybgalkaagu inuu noqdo mid la tiriyey. ", 'Jawaabahaaga waxaa loo ilaalin doonaa si qarsoodi ah waxaana loo isticmaali doonaa wadar ahaan oo keliya. ', 'Fadlan Guji Next si aad u sii wadato! ', 'Xiga '], 'st': ['Rea leboha ka ho lumela ho nka karolo phuputsong ea rona. ', "Maikutlo a hau a bohlokoa ho rona, ka mosa o fana ka likarabo tse tšepahalang le tse nahannoeng bakeng sa potso ka 'ngoe ho etsa hore karolo ea hau e nke karolo. ", "Likarabo tsa hau li tla bolokoa e le lekunutu 'me li tla sebelisoa ka kakaretso feela. ", 'Ka kopo tlanya E latelang ho Tsoelapele! ', "E 'ngoe "], 'es': ['Gracias por aceptar participar en nuestra encuesta. ', 'Sus opiniones son importantes para nosotros, tenga la amabilidad de brindar respuestas honestas y reflexivas para cada pregunta para que su participación cuente. ', 'Sus respuestas se mantendrán confidenciales y solo se utilizarán en conjunto. ', 'Haga clic en Siguiente para continuar. ', 'Siguiente '], 'su': ['Hatur nuhun parantos satuju pikeun ilubiung dina Survei Kami. ', 'Pendapat anjeun penting pikeun kami, bageur masihan réspon anu jujur sareng bijaksana pikeun tiap patarosan pikeun ngajantenkeun partisipasi anjeun diitung. ', 'Réspon anjeun bakal dijaga rahasia na bakal dipaké dina agrégat hungkul. ', 'Mangga Pencét Salajengna kanggo Teraskeun! ', 'Teras '], 'sw': ['Asante Kwa Kukubali Kushiriki Katika Utafiti Wetu. ', 'Maoni yako ni muhimu kwetu, kwa upole toa majibu ya uaminifu na ya kufikiria kwa kila swali ili kufanya ushiriki wako uhesabu. ', 'Majibu yako yatahifadhiwa kwa siri na yatatumika kwa jumla tu. ', 'Tafadhali Bonyeza Ijayo ili Kuendelea! ', 'Ifuatayo '], 'ss': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sv': ['Tack för att du gick med på att delta i vår undersökning. ', 'Dina åsikter är viktiga för oss, vänligen ge ärliga och omtänksamma svar för varje fråga för att få ditt deltagande att räknas. ', 'Dina svar kommer att hållas konfidentiella och kommer endast att användas tillsammans. ', 'Klicka på Nästa för att fortsätta! ', 'Nästa '], 'te': ['మా సర్వేలో పాల్గొనడానికి అంగీకరించినందుకు ధన్యవాదాలు. ', 'మీ అభిప్రాయాలు మాకు ముఖ్యమైనవి, మీ భాగస్వామ్యాన్ని లెక్కించడానికి ప్రతి ప్రశ్నకు నిజాయితీగా మరియు ఆలోచనాత్మకమైన ప్రతిస్పందనలను అందించండి. ', 'మీ స్పందనలు గోప్యంగా ఉంచబడతాయి మరియు మొత్తంగా మాత్రమే ఉపయోగించబడతాయి. ', 'కొనసాగించడానికి దయచేసి తదుపరి క్లిక్ చేయండి! ', 'తరువాత '], 'tg': ['Ташаккур барои розигӣ барои иштирок дар пурсиши мо. ', 'Фикрҳои шумо барои мо муҳиманд, барои ҳар як савол ҷавобҳои ростқавлона ва мулоҳизакорона пешниҳод намоед, то иштироки шумо ҳисоб карда шавад. ', 'Ҷавобҳои шумо махфӣ нигоҳ дошта мешаванд ва танҳо дар маҷмӯъ истифода мешаванд. ', 'Лутфан, ки барои идома додан Nextро клик кунед! ', 'Баъдӣ '], 'th': ['ขอขอบคุณที่ตกลงที่จะเข้าร่วมในการสำรวจของเรา ', 'ความคิดเห็นของคุณมีความสำคัญต่อเราโปรดตอบคำถามแต่ละข้ออย่างตรงไปตรงมาและรอบคอบเพื่อให้การมีส่วนร่วมของคุณมีค่า ', 'คำตอบของคุณจะถูกเก็บเป็นความลับและจะถูกใช้โดยรวมเท่านั้น ', 'กรุณาคลิกถัดไปเพื่อดำเนินการต่อ! ', 'ต่อไป '], 'ti': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'bo': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'tk': ['Anketamyza gatnaşmaga razy bolanyňyz üçin sag boluň. ', 'Pikirleriňiz biziň üçin möhümdir, gatnaşmagyňyzy hasaplamak üçin her soraga dogruçyl we oýlanyşykly jogap beriň. ', 'Jogaplaryňyz gizlin saklanar we diňe jemlener. ', 'Dowam etmek üçin "Indiki" düwmesine basmagyňyzy haýyş edýäris! ', 'Indiki '], 'tl': ['Salamat sa Pagsang-ayon na Makilahok sa Aming Survey. ', 'Ang iyong mga opinyon ay mahalaga sa amin, mabait na magbigay ng matapat at maalalahanin na mga tugon para sa bawat katanungan upang mabilang ang iyong pakikilahok. ', 'Ang iyong mga tugon ay pananatilihing kumpidensyal at gagamitin sa pinagsama-sama lamang. ', 'Mangyaring Mag-click sa Susunod upang Magpatuloy! ', 'Susunod '], 'tn': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'tr': ['Anketimize Katılmayı Kabul Ettiğiniz İçin Teşekkür Ederiz. ', 'Görüşleriniz bizim için önemlidir, katılımınızın önemli olması için her soruya dürüst ve düşünceli yanıtlar verin. ', 'Yanıtlarınız gizli tutulacak ve yalnızca toplu olarak kullanılacaktır. ', "Devam etmek için lütfen İleri'yi tıklayın! ", 'Sonraki '], 'ts': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'tt': ['Безнең тикшерүдә катнашырга ризалашкан өчен рәхмәт. ', 'Сезнең фикерләр безнең өчен мөһим, сезнең катнашуыгызны санар өчен, һәр сорауга намуслы һәм уйлы җавап бирегез. ', 'Сезнең җаваплар яшерен сакланачак һәм бары тик гомуми кулланылачак. ', 'Алга таба дәвам итегез! ', 'Алга '], 'tw': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ty': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ug': ['بىزنىڭ تەكشۈرۈشكە قاتنىشىشقا قوشۇلغانلىقىڭىزغا رەھمەت. ', 'پىكىرلىرىڭىز بىز ئۈچۈن مۇھىم ، ئىشتىراك قىلىشىڭىزنى ھېسابلاش ئۈچۈن ھەر بىر سوئالغا سەمىمىي ۋە ئەستايىدىل جاۋاب بىلەن جاۋاب بېرىڭ. ', 'ئىنكاسىڭىز مەخپىي ساقلىنىدۇ ، پەقەت ئومۇمىي جەھەتتىن ئىشلىتىلىدۇ. ', 'داۋاملاشتۇرۇش ئۈچۈن «كېيىنكى» نى چېكىڭ. ', 'كېيىنكى '], 'uk': ['Дякуємо за згоду взяти участь у нашому опитуванні. ', 'Ваші думки для нас важливі, будь ласка, надайте чесні та вдумливі відповіді на кожне запитання, щоб зробити вашу участь підрахунком. ', 'Ваші відповіді будуть конфіденційними та використовуватимуться лише в сукупності. ', 'Натисніть Далі, щоб продовжити! ', 'Далі '], 'ur': ['ہمارے سروے میں حصہ لینے کے لئے اتفاق کرنے کے لئے آپ کا شکریہ۔ ', 'آپ کی رائے ہمارے لئے اہم ہے ، براہ کرم ہر ایک سوال کے لئے دیانتدار اور سوچ سمجھ کر جوابات فراہم کریں تاکہ آپ کی شرکت کو گنتی جا سکے۔ ', 'آپ کے جوابات خفیہ رکھے جائیں گے اور صرف مجموعی میں استعمال ہوں گے۔ ', 'براہ کرم جاری رکھنے کے لئے اگلا پر کلک کریں! ', 'اگلے '], 'uz': ["So'rovnomamizda qatnashishga rozi bo'lganingiz uchun tashakkur. ", 'Sizning fikrlaringiz biz uchun muhim, har bir savolga samimiy va mulohazali javoblar bilan tashrif buyurishingizni hisobga oling. ', 'Javoblaringiz sir saqlanadi va faqat umumiy holda ishlatiladi. ', 'Davom etish uchun Keyingisini bosing! ', 'Keyingi '], 've': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'vi': ['Cảm Ơn Bạn Đã Đồng Ý Tham Gia Cuộc Khảo Sát Của Chúng Tôi. ', 'Ý kiến của bạn là quan trọng đối với chúng tôi, vui lòng cung cấp câu trả lời trung thực và chu đáo cho mỗi câu hỏi để làm cho sự tham gia của bạn có giá trị. ', 'Câu trả lời của bạn sẽ được giữ bí mật và chỉ được sử dụng tổng hợp. ', 'Vui lòng Click Next để Tiếp tục! ', 'Kế tiếp '], 'wa': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'cy': ['Diolch i chi am gytuno i gymryd rhan yn ein harolwg. ', "Mae eich barn yn bwysig i ni, yn garedig iawn yn darparu ymatebion gonest a meddylgar ar gyfer pob cwestiwn er mwyn gwneud i'ch cyfranogiad gyfrif. ", "Bydd eich ymatebion yn cael eu cadw'n gyfrinachol ac yn cael eu defnyddio fel cyfanred yn unig. ", 'Cliciwch ar Next i Barhau! ', 'Nesaf '], 'wo': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'fy': ['Tankewol foar jo akkoart mei te dwaan oan ús enkête. ', 'Jo mieningen binne wichtich foar ús, leverje freonlik earlike en skôgjende antwurden foar elke fraach om jo dielname te tellen. ', 'Jo antwurden wurde fertroulik hâlden en sille allinich yn aggregaat wurde brûkt. ', 'Klik asjebleaft Folgjende om troch te gean! ', 'Folgjende '], 'xh': ['Enkosi ngokuvuma ukuthatha inxaxheba kuvavanyo lwethu. ', 'Uluvo lwakho lubalulekile kuthi, ngobubele sinike iimpendulo ezinyanisekileyo nezicingisisiweyo kumbuzo ngamnye ukwenzela ukuba uthathe inxaxheba. ', 'Iimpendulo zakho ziya kugcinwa ziyimfihlo kwaye ziya kusetyenziswa ngokudibeneyo kuphela. ', 'Nceda ucofe ulandelayo ukuze uqhubeke! ', 'Okulandelayo '], 'yi': ['דאנק איר פֿאַר אַגריינג צו אָנטייל נעמען אין אונדזער יבערבליק. ', 'דיין מיינונגען זענען וויכטיק פֿאַר אונדז, ביטע געבן ערלעך און פאַרטראַכט ענטפֿערס פֿאַר יעדער קשיא צו מאַכן דיין באַטייליקונג ציילן. ', 'דיין ענטפֿערס וועט זיין קאַנפאַדענשאַל און וועט זיין געוויינט בלויז אין געמיינזאַם. ', 'ביטע גיט ווייַטער צו פאָרזעצן! ', 'ווייַטער '], 'yo': ['O ṣeun Fun Gbigba Lati Kopa Ninu Iwadi Wa. ', 'Awọn imọran rẹ ṣe pataki si wa, ni ifunni pese awọn idahun otitọ ati iṣaro fun ibeere kọọkan lati jẹ ki ikopa rẹ ka. ', 'Awọn idahun rẹ yoo wa ni igbekele ati pe yoo ṣee lo ni apapọ nikan. ', 'Jọwọ Tẹ Itele lati Tẹsiwaju! ', 'Itele '], 'za': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'zu': ['Ngiyabonga Ngokuvuma Ukubamba iqhaza Ocwaningweni Lwethu. ', 'Imibono yakho ibalulekile kithi, ngomusa unikeze izimpendulo ezithembekile nezicabangayo zombuzo ngamunye ukuze wenze ukubamba iqhaza kwakho kubalwe. ', 'Izimpendulo zakho zizogcinwa ziyimfihlo futhi zizosetshenziswa ekuhlanganisweni kuphela. ', 'Sicela uchofoze okulandelayo ukuze uqhubeke! ', 'Olandelayo '], 'ta': ['எங்கள் கணக்கெடுப்பில் பங்கேற்க ஒப்புக்கொண்டதற்கு நன்றி. ', 'உங்கள் கருத்துக்கள் எங்களுக்கு முக்கியம், உங்கள் பங்கேற்பைக் கணக்கிட ஒவ்வொரு கேள்விக்கும் நேர்மையான மற்றும் சிந்தனைமிக்க பதில்களை தயவுசெய்து வழங்குங்கள். ', 'உங்கள் பதில்கள் ரகசியமாக வைக்கப்படும், மேலும் அவை மொத்தத்தில் மட்டுமே பயன்படுத்தப்படும். ', 'தொடர அடுத்து என்பதைக் கிளிக் செய்க! ', 'அடுத்தது '], 'vo': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'nld': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'doi': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'kok': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'mai': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'mni': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ori': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sat': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'sot': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'chn': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'yue': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ph': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next'], 'ct': ['Thank You For Agreeing To Participate In Our Survey.', 'Your opinions are important to us, kindly provide honest and thoughtful responses for each question in order to make your participation count.', 'Your responses will be kept confidential and will be used in aggregate only.', 'Please Click Next to Continue!', 'Next']}
            
            exist_page_content = {}
            for l in language_list:
                try:
                    language_obj = Language.objects.get(language_code = l)
                    exist_language[l] = language_list[l]
                except:
                    language_obj = Language(language_code = l, language_name = language_list[l])
                    language_obj.save()
                try:
                    surveyentry_page_content_obj = SurveyEntryWelcomePageContent.objects.get(language=language_obj)
                    exist_page_content[l] = language_list[l]
                except:
                    surveyentry_page_content_obj = SurveyEntryWelcomePageContent(language=language_obj, row_1_text=page_content[l][0], row_2_text=page_content[l][1], row_3_text=page_content[l][2], row_4_text=page_content[l][3], row_5_text=page_content[l][4])
                    surveyentry_page_content_obj.save()

            currency_list = {"ADB Unit of Account" : "XUA",  "Afghani" : "AFN",  "Algerian Dinar" : "DZD",  "Argentine Peso" : "ARS",  "Armenian Dram" : "AMD",  "Aruban Florin" : "AWG",  "Australian Dollar" : "AUD",  "Azerbaijanian Manat" : "AZN",  "Bahamian Dollar" : "BSD",  "Bahraini Dinar" : "BHD",  "Baht" : "THB",  "Balboa" : "PAB",  "Barbados Dollar" : "BBD",  "Belarussian Ruble" : "BYN",  "Belize Dollar" : "BZD",  "Bermudian Dollar" : "BMD",  "Bolivar" : "VEF",  "Boliviano" : "BOB",  "Brazilian Real" : "BRL",  "Brunei Dollar" : "BND",  "Bulgarian Lev" : "BGN",  "Burundi Franc" : "BIF",  "Cabo Verde Escudo" : "CVE",  "Canadian Dollar" : "CAD",  "Cayman Islands Dollar" : "KYD",  "CFA Franc BCEAO" : "XOF",  "CFA Franc BEAC" : "XAF",  "CFP Franc" : "XPF",  "Chilean Peso" : "CLP",  "Colombian Peso" : "COP",  "Comoro Franc" : "KMF",  "Congolese Franc" : "CDF",  "Convertible Mark" : "BAM",  "Cordoba Oro" : "NIO",  "Costa Rican Colon" : "CRC",  "Cuban Peso" : "CUP",  "Czech Koruna" : "CZK",  "Dalasi" : "GMD",  "Danish Krone" : "DKK",  "Denar" : "MKD",  "Djibouti Franc" : "DJF",  "Dobra" : "STN",  "Dominican Peso" : "DOP",  "Dong" : "VND",  "East Caribbean Dollar" : "XCD",  "Egyptian Pound" : "EGP",  "El Salvador Colon" : "SVC",  "Ethiopian Birr" : "ETB",  "Euro" : "EUR",  "Falkland Islands Pound" : "FKP",  "Fiji Dollar" : "FJD",  "Forint" : "HUF",  "Ghana Cedi" : "GHS",  "Gibraltar Pound" : "GIP",  "Gourde" : "HTG",  "Guarani" : "PYG",  "Guinea Franc" : "GNF",  "Guyana Dollar" : "GYD",  "Hong Kong Dollar" : "HKD",  "Hryvnia" : "UAH",  "Iceland Krona" : "ISK",  "Indian Rupee" : "INR",  "Iranian Rial" : "IRR",  "Iraqi Dinar" : "IQD",  "Jamaican Dollar" : "JMD",  "Jordanian Dinar" : "JOD",  "Kenyan Shilling" : "KES",  "Kina" : "PGK",  "Kip" : "LAK",  "Kuna" : "HRK",  "Kuwaiti Dinar" : "KWD",  "Kwacha" : "MWK",  "Kwanza" : "AOA",  "Kyat" : "MMK",  "Lari" : "GEL",  "Lebanese Pound" : "LBP",  "Lek" : "ALL",  "Lempira" : "HNL",  "Leone" : "SLL",  "Liberian Dollar" : "LRD",  "Libyan Dinar" : "LYD",  "Lilangeni" : "SZL",  "Loti" : "LSL",  "Malagasy Ariary" : "MGA",  "Malaysian Ringgit" : "MYR",  "Mauritius Rupee" : "MUR",  "Mexican Peso" : "MXN",  "Mexican Unidad de Inversion (UDI)" : "MXV",  "Moldovan Leu" : "MDL",  "Moroccan Dirham" : "MAD",  "Mozambique Metical" : "MZN",  "Mvdol" : "BOV",  "Naira" : "NGN",  "Nakfa" : "ERN",  "Namibia Dollar" : "NAD",  "Nepalese Rupee" : "NPR",  "Netherlands Antillean Guilder" : "ANG",  "New Israeli Sheqel" : "ILS",  "New Taiwan Dollar" : "TWD",  "New Zealand Dollar" : "NZD",  "Ngultrum" : "BTN",  "North Korean Won" : "KPW",  "Norwegian Krone" : "NOK",  "Nuevo Sol" : "PEN",  "Ouguiya" : "MRU",  "Pa’anga" : "TOP",  "Pakistan Rupee" : "PKR",  "Pataca" : "MOP",  "Peso Convertible" : "CUC",  "Peso Uruguayo" : "UYU",  "Philippine Peso" : "PHP",  "Pound Sterling" : "GBP",  "Pula" : "BWP",  "Qatari Rial" : "QAR",  "Quetzal" : "GTQ",  "Rand" : "ZAR",  "Rial Omani" : "OMR",  "Riel" : "KHR",  "Romanian Leu" : "RON",  "Rufiyaa" : "MVR",  "Rupiah" : "IDR",  "Russian Ruble" : "RUB",  "Rwanda Franc" : "RWF",  "Saint Helena Pound" : "SHP",  "Saudi Riyal" : "SAR",  "SDR (Special Drawing Right)" : "XDR",  "Serbian Dinar" : "RSD",  "Seychelles Rupee" : "SCR",  "Singapore Dollar" : "SGD",  "Solomon Islands Dollar" : "SBD",  "Som" : "KGS",  "Somali Shilling" : "SOS",  "Somoni" : "TJS",  "South Sudanese Pound" : "SSP",  "Sri Lanka Rupee" : "LKR",  "Sucre" : "XSU",  "Sudanese Pound" : "SDG",  "Surinam Dollar" : "SRD",  "Swedish Krona" : "SEK",  "Swiss Franc" : "CHF",  "Syrian Pound" : "SYP",  "Taka" : "BDT",  "Tala" : "WST",  "Tanzanian Shilling" : "TZS",  "Tenge" : "KZT",  "Trinidad and Tobago Dollar" : "TTD",  "Tugrik" : "MNT",  "Tunisian Dinar" : "TND",  "Turkish Lira" : "TRY",  "Turkmenistan New Manat" : "TMT",  "UAE Dirham" : "AED",  "Uganda Shilling" : "UGX",  "Unidad de Fomento" : "CLF",  "Unidad de Valor Real" : "COU",  "Uruguay Peso en Unidades Indexadas (URUIURUI)" : "UYI",  "US Dollar" : "USD",  "US Dollar (Next day)" : "USN",  "Uzbekistan Sum" : "UZS",  "Vatu" : "VUV",  "WIR Euro" : "CHE",  "WIR Franc" : "CHW",  "Won" : "KRW",  "Yemeni Rial" : "YER",  "Yen" : "JPY",  "Yuan Renminbi" : "CNY",  "Zambian Kwacha" : "ZMW",  "Zimbabwe Dollar" : "ZWL",  "Zloty" : "PLN"}
            exist_currency = {}
            for cur in currency_list:
                try:
                    currenct_obj = Currency.objects.get(currency_name = cur)
                    exist_currency[cur] = currency_list[cur]
                    pass
                except:
                    currenct_obj = Currency(currency_name = cur, currency_iso = currency_list[cur])
                    currenct_obj.save()

            question_category_list = ['DEMO', 'ADHOC', 'Airlines/Travel', 'Arts/Entertainment/Films', 'Automotive', 'B2B/Employment', 'Banking/Finance', 'Beverages', 'Demographic', 'Education', 'Electronics/Computer/Software', 'Food/Snacks', 'Hobbies/Sports', 'Home/Family/Children', 'Household', 'IT/Digital/Software', 'Medical/Health', 'Other', 'Panel Recruit', 'Politics/Religion', 'Tobacco/Gambling', 'Red Herring']
            
            exist_question_category = []
            for question_category in question_category_list:
                try:
                    question_obj = QuestionCategory.objects.get(category = question_category)
                    exist_question_category.append(question_category)
                    pass
                except:
                    question_obj = QuestionCategory(category = question_category)
                    question_obj.save()

            # ********************** Check Three Conditions *************************
            if exist_permissions == group_name_list and exist_country != country_list and exist_language == language_list and exist_currency == currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Group, Language, Currency and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions == group_name_list and exist_country == country_list and exist_language != language_list and exist_currency == currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Group, Country, Currency and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions == group_name_list and exist_country == country_list and exist_language == language_list and exist_currency != currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Group, Country, Language and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions == group_name_list and exist_country == country_list and exist_language == language_list and exist_currency == currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Group, Country, Language and Currency already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country == country_list and exist_language == language_list and exist_currency == currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Country, Language, Currency and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            
            # ********************** Check Two Conditions *************************
            if exist_permissions == group_name_list and exist_country == country_list and exist_language != language_list and exist_currency!= currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Group and Country already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions == group_name_list and exist_country != country_list and exist_language == language_list and exist_currency != currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Group and Language already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions == group_name_list and exist_country != country_list and exist_language != language_list and exist_currency == currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Group and Currency already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions == group_name_list and exist_country != country_list and exist_language != language_list and exist_currency != currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Group and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country == country_list and exist_language == language_list and exist_currency != currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Country and Langugae already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country == country_list and exist_language != language_list and exist_currency == currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Country and Currency already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country == country_list and exist_language != language_list and exist_currency != currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Country and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country != country_list and exist_language == language_list and exist_currency == currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Language and Currency already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country != country_list and exist_language == language_list and exist_currency != currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Language and Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            
            # ********************** Check One Conditions *************************
            if exist_permissions == group_name_list and exist_country != country_list and exist_language != language_list and exist_currency != currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Group already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country == country_list and exist_language != language_list and exist_currency != currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Country already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country != country_list and exist_language == language_list and exist_currency != currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Language already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country != country_list and exist_language != language_list and exist_currency == currency_list and exist_question_category != question_category_list:
                return Response({'error': 'Currency already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            if exist_permissions != group_name_list and exist_country != country_list and exist_language != language_list and exist_currency != currency_list and exist_question_category == question_category_list:
                return Response({'error': 'Question Category already exist but other data are created sucessfully..!'}, status=status.HTTP_200_OK)
            
            if exist_permissions == group_name_list and exist_country == country_list and exist_language == language_list and exist_currency == currency_list and exist_question_category == question_category_list and exist_page_content == page_content:
                return Response({'error': 'Initial setup already exist..!'}, status=status.HTTP_400_BAD_REQUEST)
            
            emp = EmployeeProfile.objects.create(email = 'admin@gmail.com',first_name = 'admin',last_name = 'panel',is_superuser = True,contact_number = '+1234567890',country_id = 110,zipcode = '12345',is_admin = True,is_staff=True)
            emp.set_password("12345678")
            emp.user_permissions.set(Permission.objects.all())
            emp.groups.set(Group.objects.all())
            emp.save()
            
            #create Toluna Zamplia Lucid Customer for Survey Fetch
            tolunacust = CustomerOrganization.objects.create(payment_terms = 2500 ,cust_org_name = 'Toluna Customer',customer_organization_type = '1',cust_org_country_id = 110,customer_url_code = 'toluna',sales_person_id_id = 1,currency_id = 62,customer_invoice_currency_id = 62)
            ClientContact.objects.create(client_firstname = 'toluna',client_lastname= 'customer',client_email = 'admin@gmail.com',customer_id_id = tolunacust.id)
            
            zampliacust = CustomerOrganization.objects.create(payment_terms = 2500 ,cust_org_name = 'Zamplia Customer',customer_organization_type = '1',cust_org_country_id = 110,customer_url_code = 'zamplia',sales_person_id_id = 1,currency_id = 62,customer_invoice_currency_id = 62)
            ClientContact.objects.create(client_firstname = 'zamplia',client_lastname= 'customer',client_email = 'admin@gmail.com',customer_id_id = zampliacust.id)
            
            lucidcust = CustomerOrganization.objects.create(payment_terms = 2500 ,cust_org_name = 'Lucid Customer',customer_organization_type = '1',cust_org_country_id = 110,customer_url_code = 'lucid',sales_person_id_id = 1,currency_id = 62,customer_invoice_currency_id = 62)
            ClientContact.objects.create(client_firstname = 'lucid',client_lastname= 'customer',client_email = 'admin@gmail.com',customer_id_id = lucidcust.id)
            
            customer_qs = CustomerOrganization.objects.filter(customer_url_code = 'toluna')

            ClientDBCountryLanguageMapping.objects.filter(customer=customer_qs[0]).delete()

            headers = {'PARTNER_AUTH_KEY': settings.TOLUNA_PARTNER_AUTH_KEY,'Content-Type':'application/json'}

            response = requests.get(f'{settings.TOLUNA_CLIENT_BASE_SETUP_URL}/IPUtilityService/ReferenceData/Cultures', headers=headers)


            country_lang_list = []
            for item in response.json():
                try:
                    country_obj = Country.objects.get(country_code=(item['Name'].split('-')[1].upper()))
                    language_obj = Language.objects.get(language_code=item['Name'].split('-')[0])
                    country_lang_list.append(ClientDBCountryLanguageMapping(customer=customer_qs[0], lanugage_id=language_obj, country_id=country_obj, toluna_client_language_id=item['CultureID'], client_language_description=item['Description'], client_language_name=item['Name']))
                except:
                    pass
            ClientDBCountryLanguageMapping.objects.bulk_create(country_lang_list)
            
            # SETUP CURRENCY DATA FROM THE CLIENT API TO OUR DB
            response = requests.get(f'{settings.TOLUNA_CLIENT_BASE_SETUP_URL}/IPUtilityService/ReferenceData/Currencies', headers=headers)

            currency_list = []
            for item in response.json():
                currency_list.append(Currency(client_currency_id=item['CurrencyID'], client_currency_name=item['Name'], customer_name=customer_qs[0].customer_url_code))

            Currency.objects.filter(customer_name='toluna').delete()
            Currency.objects.bulk_create(currency_list)

            # SETUP STUDY TYPE DATA FROM THE CLIENT API TO OUR DB
            response = requests.get(f'{settings.TOLUNA_CLIENT_BASE_SETUP_URL}/IPUtilityService/ReferenceData/StudyTypes', headers=headers)
            
            
            # SETUP QUESTION CATEGORIES FROM THE CLIENT API TO OUR DB
            response = requests.get(f'{settings.TOLUNA_CLIENT_BASE_SETUP_URL}/IPUtilityService/ReferenceData/QuestionCategories', headers=headers)
            currency_list2 = []
            for item in response.json():
                currency_list2.append(QuestionCategory(category=item['Name'], category_description=item['Description'], category_id=item['CategoryID']))

            QuestionCategory.objects.bulk_create(currency_list2)

            #Zamplia Country Lang Mapping
            data_dict = [
                {
                    "country_id__country_code": "AR",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "8"
                },
                {
                    "country_id__country_code": "AT",
                    "lanugage_id__language_code": "de",
                    "zamplia_client_language_id": "10"
                },
                {
                    "country_id__country_code": "AU",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "9"
                },
                {
                    "country_id__country_code": "BD",
                    "lanugage_id__language_code": "bn",
                    "zamplia_client_language_id": "73"
                },
                {
                    "country_id__country_code": "BR",
                    "lanugage_id__language_code": "pt",
                    "zamplia_client_language_id": "13"
                },
                {
                    "country_id__country_code": "CH",
                    "lanugage_id__language_code": "fr",
                    "zamplia_client_language_id": "50"
                },
                {
                    "country_id__country_code": "CH",
                    "lanugage_id__language_code": "de",
                    "zamplia_client_language_id": "49"
                },
                {
                    "country_id__country_code": "CL",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "16"
                },
                {
                    "country_id__country_code": "CO",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "18"
                },
                {
                    "country_id__country_code": "CR",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "19"
                },
                {
                    "country_id__country_code": "DE",
                    "lanugage_id__language_code": "de",
                    "zamplia_client_language_id": "24"
                },
                {
                    "country_id__country_code": "DO",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "69"
                },
                {
                    "country_id__country_code": "EC",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "21"
                },
                {
                    "country_id__country_code": "EG",
                    "lanugage_id__language_code": "ar",
                    "zamplia_client_language_id": "22"
                },
                {
                    "country_id__country_code": "ES",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "47"
                },
                {
                    "country_id__country_code": "FR",
                    "lanugage_id__language_code": "fr",
                    "zamplia_client_language_id": "23"
                },
                {
                    "country_id__country_code": "GH",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "62"
                },
                {
                    "country_id__country_code": "GT",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "70"
                },
                {
                    "country_id__country_code": "HK",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "25"
                },
                {
                    "country_id__country_code": "ID",
                    "lanugage_id__language_code": "id",
                    "zamplia_client_language_id": "26"
                },
                {
                    "country_id__country_code": "IE",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "27"
                },
                {
                    "country_id__country_code": "IT",
                    "lanugage_id__language_code": "it",
                    "zamplia_client_language_id": "28"
                },
                {
                    "country_id__country_code": "JM",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "64"
                },
                {
                    "country_id__country_code": "KE",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "61"
                },
                {
                    "country_id__country_code": "MY",
                    "lanugage_id__language_code": "ms",
                    "zamplia_client_language_id": "30"
                },
                {
                    "country_id__country_code": "NG",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "34"
                },
                {
                    "country_id__country_code": "NL",
                    "lanugage_id__language_code": "nl",
                    "zamplia_client_language_id": "32"
                },
                {
                    "country_id__country_code": "NZ",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "33"
                },
                {
                    "country_id__country_code": "PA",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "71"
                },
                {
                    "country_id__country_code": "PE",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "36"
                },
                {
                    "country_id__country_code": "PL",
                    "lanugage_id__language_code": "pl",
                    "zamplia_client_language_id": "38"
                },
                {
                    "country_id__country_code": "PR",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "60"
                },
                {
                    "country_id__country_code": "PR",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "59"
                },
                {
                    "country_id__country_code": "PY",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "66"
                },
                {
                    "country_id__country_code": "PY",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "65"
                },
                {
                    "country_id__country_code": "QA",
                    "lanugage_id__language_code": "ar",
                    "zamplia_client_language_id": "40"
                },
                {
                    "country_id__country_code": "RU",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "42"
                },
                {
                    "country_id__country_code": "RU",
                    "lanugage_id__language_code": "ru",
                    "zamplia_client_language_id": "41"
                },
                {
                    "country_id__country_code": "TH",
                    "lanugage_id__language_code": "th",
                    "zamplia_client_language_id": "52"
                },
                {
                    "country_id__country_code": "AE",
                    "lanugage_id__language_code": "ar",
                    "zamplia_client_language_id": "56"
                },
                {
                    "country_id__country_code": "BE",
                    "lanugage_id__language_code": "de",
                    "zamplia_client_language_id": "67"
                },
                {
                    "country_id__country_code": "BE",
                    "lanugage_id__language_code": "fr",
                    "zamplia_client_language_id": "12"
                },
                {
                    "country_id__country_code": "BE",
                    "lanugage_id__language_code": "nl",
                    "zamplia_client_language_id": "11"
                },
                {
                    "country_id__country_code": "CA",
                    "lanugage_id__language_code": "fr",
                    "zamplia_client_language_id": "15"
                },
                {
                    "country_id__country_code": "CA",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "14"
                },
                {
                    "country_id__country_code": "CN",
                    "lanugage_id__language_code": "zh",
                    "zamplia_client_language_id": "17"
                },
                {
                    "country_id__country_code": "DK",
                    "lanugage_id__language_code": "da",
                    "zamplia_client_language_id": "20"
                },
                {
                    "country_id__country_code": "GB",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "54"
                },
                {
                    "country_id__country_code": "IN",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "7"
                },
                {
                    "country_id__country_code": "IN",
                    "lanugage_id__language_code": "hi",
                    "zamplia_client_language_id": "6"
                },
                {
                    "country_id__country_code": "JP",
                    "lanugage_id__language_code": "ja",
                    "zamplia_client_language_id": "29"
                },
                {
                    "country_id__country_code": "KR",
                    "lanugage_id__language_code": "ko",
                    "zamplia_client_language_id": "46"
                },
                {
                    "country_id__country_code": "MX",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "31"
                },
                {
                    "country_id__country_code": "NO",
                    "lanugage_id__language_code": "no",
                    "zamplia_client_language_id": "35"
                },
                {
                    "country_id__country_code": "PH",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "37"
                },
                {
                    "country_id__country_code": "PT",
                    "lanugage_id__language_code": "pt",
                    "zamplia_client_language_id": "39"
                },
                {
                    "country_id__country_code": "SA",
                    "lanugage_id__language_code": "ar",
                    "zamplia_client_language_id": "43"
                },
                {
                    "country_id__country_code": "SE",
                    "lanugage_id__language_code": "sv",
                    "zamplia_client_language_id": "48"
                },
                {
                    "country_id__country_code": "SG",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "44"
                },
                {
                    "country_id__country_code": "TR",
                    "lanugage_id__language_code": "tr",
                    "zamplia_client_language_id": "53"
                },
                {
                    "country_id__country_code": "UA",
                    "lanugage_id__language_code": "uk",
                    "zamplia_client_language_id": "55"
                },
                {
                    "country_id__country_code": "UG",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "63"
                },
                {
                    "country_id__country_code": "US",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "4"
                },
                {
                    "country_id__country_code": "US",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "57"
                },
                {
                    "country_id__country_code": "UY",
                    "lanugage_id__language_code": "es",
                    "zamplia_client_language_id": "72"
                },
                {
                    "country_id__country_code": "VN",
                    "lanugage_id__language_code": "vi",
                    "zamplia_client_language_id": "58"
                },
                {
                    "country_id__country_code": "ZA",
                    "lanugage_id__language_code": "en",
                    "zamplia_client_language_id": "45"
                }
            ]
            
            for i in data_dict:
                try:
                    data = ClientDBCountryLanguageMapping.objects.get(country_id__country_code = i['country_id__country_code'], lanugage_id__language_code = i['lanugage_id__language_code'])
                    data.zamplia_client_language_id = i['zamplia_client_language_id']
                    data.save()
                except:
                    continue

            #Disq Price Setup
            cpi_list = [[1, 2.78, 2.69, 2.52, 2.48, 2.22, 2.18, 2.01, 1.88, 1.83, 1.62, 1.41, 1.20],[1, 3.80, 3.63, 3.55, 3.25, 2.86, 2.74, 2.48, 2.39, 2.22, 1.92, 1.62, 1.37],[1, 4.70, 4.53, 4.23, 3.98, 3.46, 3.29, 3.04, 2.86, 2.65, 2.22, 1.75, 1.50],[1, 6.50, 6.20, 5.69, 5.13, 4.45, 4.06, 3.63, 3.38, 3.16, 2.52, 2.01, 1.71],[1, 7.10, 6.80, 6.20, 5.94, 5.21, 4.83, 4.32, 4.02, 3.63, 2.99, 2.35, 1.92],[1, 8.25, 7.87, 7.40, 6.97, 5.99, 5.51, 5.00, 4.57, 4.23, 3.42, 2.65, 2.18],[1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]]
            loi_list = [[1,5],[6,10],[11,15],[16,20],[21,25],[26,30],[31,200]]
            incidence_list = [[1,9],[10,14],[15,19],[20,24],[25,29],[30,34],[35,39],[40,44],[45,49],[50,59],[60,69],[70,79],[80,100]]
            
            for i in range(len(loi_list)):
                for j in range(len(incidence_list)):
                    cpi = cpi_list[i][j]
                    
                    min_loi = loi_list[i][0]
                    max_loi = loi_list[i][1]
                    
                    min_incidence = incidence_list[j][0]
                    max_incidence = incidence_list[j][1]

                    DisqoAPIPricing.objects.get_or_create(
                        min_loi = min_loi,
                        max_loi = max_loi,
                        min_incidence = min_incidence,
                        max_incidence = max_incidence,
                        cpi = cpi
                    )
            
            #Lucid Country Lang Mapping For API Supplier
            LucidCountryLanguageMapping.objects.all().delete()

            headers = {'Authorization': '72E92E75-D1CF-4190-974C-DA7E8F1F139C'}

            response = requests.get('https://sandbox.techops.engineering/Lookup/v1/BasicLookups/BundledLookups/CountryLanguages', headers=headers)

            responses_dict = {item['Name']:item for item in response.json()['AllCountryLanguages']}

            for item in response.json()['AllCountryLanguages']:
                if item['Name'].split('-')[1].replace(' ','') == 'RepublicoftheCongo':
                    country_obj = Country.objects.get(country_name='Congo - Kinshasa')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'HongKong':
                    country_obj = Country.objects.get(country_name='Hong Kong SAR China')
                    if item['Name'].split('-')[0][:-1] == 'Chinese Traditional':
                        language_obj = Language.objects.get(language_name='Chinese')
                    else:
                        language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'TaiwanProvinceOfChina':
                    country_obj = Country.objects.get(country_name='Taiwan')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'Slovakia(SlovakRepublic)':
                    country_obj = Country.objects.get(country_name='Slovakia')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'LibyanArabJamahiriya':
                    country_obj = Country.objects.get(country_name='Libya')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'Myanmar':
                    country_obj = Country.objects.get(country_name='Myanmar [Burma]')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'RepublicoftheCôted\'Ivoire':
                    country_obj = Country.objects.get(country_name='Cote DIvoire')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') in ('SãoToméandPríncipe','SaoTomeAndPrincipe'):
                    country_obj = Country.objects.get(country_name='Sao Tome and Principe')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'DemocraticRepublicoftheCongo':
                    country_obj = Country.objects.get(country_name='Congo - Brazzaville')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'Korea':
                    country_obj = Country.objects.get(country_name='North Korea')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','') == 'Palestine':
                    country_obj = Country.objects.get(country_name='Palestinian Territories')
                    language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                elif item['Name'].split('-')[1].replace(' ','')[1:].isupper() != True and item['Name'].split('-')[1].replace(' ','')[1:].islower() != True:
                    country_full_name = item['Name'].split('-')[1].replace(' ','')
                    country_sliced_name = item['Name'].split('-')[1].replace(' ','')[1:]
                    country_name_list = []
                    country_name_list.extend(country_full_name)
                    uppercase_frequency = 0
                    for string in country_sliced_name:
                        if string.isupper() == True:
                            uppercase_frequency+=1
                            if uppercase_frequency > 2:
                                position = country_sliced_name.index(string)
                                country_name_list.insert(position+3,'^')
                            elif uppercase_frequency > 1:
                                position = country_sliced_name.index(string)
                                country_name_list.insert(position+2,'^')
                            else:
                                position = country_sliced_name.index(string)
                                country_name_list.insert(position+1,'^')
                    final_country_name_str = ''.join(country_name_list).replace('^',' ')
                    try:
                        country_obj = Country.objects.get(country_name=final_country_name_str)
                    except:
                        continue
                    if item['Name'].split('-')[0][:-1] in ('Chinese Simplified','Chinese Traditional'):
                        language_obj = Language.objects.get(language_name='Chinese')
                    else:
                        language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                else:
                    try:
                        country_obj = Country.objects.get(country_name=(item['Name'].split('-'))[1].replace(' ','') if len(item['Name'].split('-')) == 2 else '-'.join(item['Name'].split('-')[1:]).replace(' ',''))
                    except:
                        continue
                    if item['Name'].split('-')[0][:-1] in ('Chinese Traditional','Chinese Simplified'):
                        language_obj = Language.objects.get(language_name='Chinese')
                    elif item['Name'].split('-')[0][:-1] == 'Luxembourg':
                        language_obj = Language.objects.get(language_name='Luxembourgish')
                    elif item['Name'].split('-')[0][:-1] == 'Slovene':
                        language_obj = Language.objects.get(language_name='Slovenian')
                    elif item['Name'].split('-')[0][:-1] == 'Gujrati':
                        language_obj = Language.objects.get(language_name='Gujarati')
                    elif item['Name'].split('-')[0][:-1] == 'Bokmal':
                        language_obj = Language.objects.get(language_name='Norwegian Bokmal')
                    elif item['Name'].split('-')[0][:-1] in ('Flemish','Dogri','Konkani','Maithili','Manipuri','Odia','Santali','Sesotho','Chinese Simplified','Cantonese'):
                        # These Languages do not exist in our DB
                        continue
                    else:
                        try:
                            language_obj = Language.objects.get(language_name=item['Name'].split('-')[0][:-1])
                        except:
                            continue

                country_lang_id = responses_dict[item['Name']]['Id']
                country_lang_code = responses_dict[item['Name']]['Code']
                country_lang_name = responses_dict[item['Name']]['Name']
                try:
                    LucidCountryLanguageMapping.objects.create(lanugage_id=language_obj, country_id=country_obj, lucid_country_lang_id=country_lang_id, lucid_language_code=country_lang_code, lucid_language_name=country_lang_name)
                except:
                    continue
            return Response({'message': 'Intial Setup Created Sucessfully...!'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Server...!'}, status=status.HTTP_400_BAD_REQUEST)

def standard_question_view():
    standard_question_answers = {
        'InitialSetup/US_questions.json' : 'InitialSetup/US_answers.json',
        'InitialSetup/Ind_questions.json' : 'InitialSetup/Ind_answers.json',
        'InitialSetup/Aus_questions.json' : 'InitialSetup/Aus_answers.json'
    }

    question_category = {
        1001 : "DEMO",
        1002 : "ADHOC",
        1003 : "Airlines/Travel/Shopping",
        1004 : "Arts/Entertainment/Films",
        1005 : "Automotive",
        1006 : "B2B/Employment",
        1007 : "Banking/Finance",
        1008 : "Demographic",
        1009 : "Education",
        1010 : "Electronics/Computer/Software",
        1011 : "Food/Snacks/Beverages",
        1012 : "Hobbies/Sports/Games",
        1013 : "Home/Family/Children",
        1014 : "Household",
        1015 : "IT/Digital/Software",
        1016 : "Medical/Health",
        1017 : "Panel Recruit",
        1018 : "Politics/Religion",
        1019 : "Tobacco/Gambling",
        1020 : "Other",
        1021 : "Basic Profiles",
    }
    for key,value in question_category.items():
        QuestionCategory.objects.update_or_create(
            category_id = key,defaults = {"category" : value}
        )

    # Question Answer Mapping from Json
    for questions,answers in standard_question_answers.items():
        question_list = json.load(open(questions,encoding="utf8"))
        answer_list = json.load(open(answers,encoding="utf8"))

        def question_mapping(question):
            if question['toluna_is_routable'] == "":
                question['toluna_is_routable'] = False
            if question['zamplia_is_routable'] == "":
                question['zamplia_is_routable'] = False
            question_category_obj = QuestionCategory.objects.get(category_id = int(question['question_category_id']))
            obj , created = ParentQuestion.objects.update_or_create(
                parent_question_number = question['Internal_question_id'],
                defaults={
                    "is_active" : question['is_active'],
                    "parent_question_category" : question_category_obj,
                    "parent_question_prescreener_type" : 'Standard',
                    "toluna_question_id" : question['toluna_question_id'],
                    "parent_question_text" : question['Question_text'],
                    "internal_parent_question_text" : question['Internal_Question_text'],
                    "parent_question_type" : question['parent_question_type'],
                    "toluna_is_routable" : question['toluna_is_routable'],
                    "toluna_question_category_id" : question['toluna_question_category_id'],
                    "disqo_question_key" : question['disqo_question_key'],
                    "disqo_question_id" : question['disqo_question_id'],
                    "zamplia_question_id" : question['zamplia_question_number'],
                    "zamplia_is_routable" : question['zamplia_is_routable'],
                    "lucid_question_id" : question['lucid_question_id'],
                    "apidbcountrylangmapping_id" : int(question['countrylang_id']),
                    "sago_question_id" : question['sago_question_id'],
                }
            )
            TranslatedQuestion.objects.filter(
                parent_question__id = obj.id).update(
                    is_active = question['is_active'],
                    parent_question_prescreener_type = 'Standard',
                    Internal_question_id = question['Internal_question_id'],
                    toluna_question_id = question['toluna_question_id'],
                    translated_question_text = question['Question_text'],
                    internal_question_text = question['Internal_Question_text'],
                    parent_question_type = question['parent_question_type'],
                    toluna_is_routable = question['toluna_is_routable'],
                    toluna_question_category_id = question['toluna_question_category_id'],
                    disqo_question_key = question['disqo_question_key'],
                    disqo_question_id = question['disqo_question_id'],
                    zamplia_question_id = question['zamplia_question_number'],
                    lucid_question_id = question['lucid_question_id'],
                    zamplia_is_routable = question['zamplia_is_routable'],
                    parent_question_category = question_category_obj,
                    apidbcountrylangmapping_id = int(question['countrylang_id']),
                    sago_question_id = question['sago_question_id'],
                )
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield_results = list(executor.map(question_mapping, question_list))
        def answer_mapping(answer):
            obj , created = ParentAnswer.objects.update_or_create(
                parent_answer_id = answer['internal_answer_id'],
                defaults={
                    "internal_question_id" : answer['Internal_question_id'],
                    "toluna_answer_id" : answer['Toluna AnswerID'],
                    "parent_answer_text" : answer['Translation answer text'],
                    "answer_internal_name" : answer['AnswerInternalName'],
                    "toluna_question_id" : answer['Toluna QuestionID'],
                    "disqo_answer_id" : answer['Disqo AnswerID'],
                    "disqo_question_key" : answer['Disqo_Question_Key'],
                    "disqo_question_id" : answer['Disqo_Question_ID'],
                    "zamplia_answer_id" : answer['ZampliaAnswerID'],
                    "zamplia_question_id" : answer['ZampliaQuestionID'],
                    "lucid_answer_id" : answer['lucid_answer_id'],
                    "lucid_question_id" : answer['lucid_question_id'],
                    "sago_answer_id" : answer['sago_answer_id'],
                    "sago_question_id" : answer['sago_question_id'],
                }
            )
            TranslatedAnswer.objects.filter(
                parent_answer__id = obj.id).update(
                    internal_answer_id = answer['internal_answer_id'],
                    internal_question_id = answer['Internal_question_id'],
                    toluna_answer_id = answer['Toluna AnswerID'],
                    translated_answer = answer['Translation answer text'],
                    answer_internal_name = answer['AnswerInternalName'],
                    toluna_question_id = answer['Toluna QuestionID'],
                    disqo_answer_id = answer['Disqo AnswerID'],
                    disqo_question_key = answer['Disqo_Question_Key'],
                    disqo_question_id = answer['Disqo_Question_ID'],
                    zamplia_answer_id = answer['ZampliaAnswerID'],
                    zamplia_question_id = answer['ZampliaQuestionID'],
                    lucid_answer_id = answer['lucid_answer_id'],
                    lucid_question_id = answer['lucid_question_id'],
                    sago_answer_id = answer['sago_answer_id'],
                    sago_question_id = answer['sago_question_id'],
                )
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield_results = list(executor.map(answer_mapping, answer_list))

        parent_questions = ParentQuestion.objects.filter(is_active = True,parent_question_prescreener_type = 'Standard')
        def parent_answer_obj_map(index):
            try:
                ParentAnswer.objects.filter(internal_question_id = index.parent_question_number).update(parent_question_id=index.id)
            except:
                pass
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield_results = list(executor.map(parent_answer_obj_map, parent_questions))

        trans_questions = TranslatedQuestion.objects.filter(is_active = True,parent_question__parent_question_prescreener_type = 'Standard')
        def translated_answer_obj_map(qu):
            try:
                TranslatedAnswer.objects.filter(internal_question_id = qu.Internal_question_id).update(translated_parent_question=qu.id)
            except:
                pass
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            yield_results = list(executor.map(translated_answer_obj_map, trans_questions))

class StandardQuestionView(APIView):

    def post(self, request):
        
        standard_question_view()
        # Zipcode mapping For CTZIP question/answers
        # it was mapped becouse toluna takes zipcode agains CTZIP questions answers
             
        zipcode_list = json.load(open('InitialSetup/US_zipcodes.json'))

        def parellel_zipcode_storing_func(zipcode):
            bulkcreatelist = []
            trans_ans_id = TranslatedAnswer.objects.filter(toluna_answer_id = zipcode[list(zipcode.keys())[0]])
            for trans_id in trans_ans_id:
                bulkcreatelist.append(
                    ZipCodeMappingTable(zipcode = list(zipcode.keys())[0],parent_answer_id = trans_id))
            ziplist = ZipCodeMappingTable.objects.bulk_create(bulkcreatelist)
        for key,value in zipcode_list.items():
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                yield_results = list(executor.map(parellel_zipcode_storing_func, value))
        return Response({"message":"Question/Answers Created/updated Successfully..!"}, status=status.HTTP_200_OK)
    


class SupplierOrgAuthKeyDetailsSetupAPI(APIView):
    
    def post(self,request):
        if settings.SERVER_TYPE == 'localhost':
            #Toluna US/India GUID Add For Pull Survey
            ClientDBCountryLanguageMapping.objects.filter(toluna_client_language_id = '1').update(country_lang_guid = '6661984C-D520-4FF0-9B9F-2B5A57CEB7A6')
            ClientDBCountryLanguageMapping.objects.filter(toluna_client_language_id = '18').update(country_lang_guid = 'C1412C3C-EA9D-4E2B-8FAE-159457DB0F19')
            return Response({"message":"OrgAuthKeySetupAPI Created/updated Successfully..!"}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid Server...!'}, status=status.HTTP_400_BAD_REQUEST)