from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, RadioField, SelectField, FormField, HiddenField
from wtforms.validators import DataRequired, Email

class ParticipantLoginForm(FlaskForm):
    pid = StringField('Participant ID', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Sign In')

class TIPI(FlaskForm):
    tipi_1 = RadioField("1.- Extraverted, enthusiastic.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_2 = RadioField("2- Critical, quarrelsome.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_3 = RadioField("3.- Dependable, self-disciplined.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_4 = RadioField("4.- Anxious, easily upset.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_5 = RadioField("5.- Open to new experiences, complex.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_6 = RadioField("6.- Reserved, quiet.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_7 = RadioField("7.- Sympathetic, warm.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_8 = RadioField("8.- Disorganized, careless.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_9 = RadioField("9.- Calm, emotionally stable.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    tipi_10 = RadioField("10.- Conventional, uncreative.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])

class PANAS(FlaskForm):
    panas_1 = RadioField("1.- Interested.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_2 = RadioField("2- Distressed.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_3 = RadioField("3.- Excited.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_4 = RadioField("4.- Upset.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_5 = RadioField("5.- Strong.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_6 = RadioField("6.- Guilty.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_7 = RadioField("7.- Scared.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_8 = RadioField("8.- Hostile.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_9 = RadioField("9.- Enthusiastic.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_10 = RadioField("10.- Proud.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_11 = RadioField("11.- Irritable.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_12 = RadioField("12- Alert.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_13 = RadioField("13.- Ashamed.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_14 = RadioField("14.- Inspired.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_15 = RadioField("15.- Nervous.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_16 = RadioField("16.- Determined.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_17 = RadioField("17.- Attentive.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_18 = RadioField("18.- Jittery.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_19 = RadioField("19.- Active.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])
    panas_20 = RadioField("20.- Afraid.", choices=[(i,i) for i in range(1,6)], validators=[DataRequired()])


class STOMPR(FlaskForm):
    stompr_1 = RadioField("1.- Alternative.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_2 = RadioField("2.- Bluegrass.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_3 = RadioField("3.- Blues.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_4 = RadioField("4.- Classical.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_5 = RadioField("5.- Country.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_6 = RadioField("6.- Dance/Electronica.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_7 = RadioField("7.- Folk.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_8 = RadioField("8.- Funk.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_9 = RadioField("9.- Gospel.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_10 = RadioField("10.- Heavy Metal.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_11 = RadioField("11.- World.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_12 = RadioField("12- Jazz.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_13 = RadioField("13.- New Age.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_14 = RadioField("14.- Oldies.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_15 = RadioField("15.- Opera.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_16 = RadioField("16.- Pop.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_17 = RadioField("17.- Punk.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_18 = RadioField("18.- Rap/hip-hop.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_19 = RadioField("19.- Reggae.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_20 = RadioField("20.- Religious.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_21 = RadioField("21.- Rock.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_22 = RadioField("22.- Soul/R&B.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    stompr_23 = RadioField("23.- Soundtracks/theme song.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])

class GMS(FlaskForm):
    gms_1 = RadioField("1.- I spend a lot of my free time doing music-related activities.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_2 = RadioField("2- I sometimes choose music that can trigger shivers down my spine.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_3 = RadioField("3.- I enjoy writing about music, for example on blogs and forums.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_4 = RadioField("4.- If somebody starts singing a song I don’t know, I can usually join in.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_5 = RadioField("5.- I am able to judge whether someone is a good singer or not.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_6 = RadioField("6.- I usually know when I’m hearing a song for the first time.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_7 = RadioField("7.- I can sing or play music from memory.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_8 = RadioField("8.- I’m intrigued by musical styles I’m not familiar with and want to find out more.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_9 = RadioField("9.- Pieces of music rarely evoke emotions for me.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_10 = RadioField("10.- I am able to hit the right notes when I sing along with a recording.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_11 = RadioField("11.- I find it difficult to spot mistakes in a performance of a song even if I know the tune.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_12 = RadioField("12- I can compare and discuss differences between two performances or versions of the same piece of music.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_13 = RadioField("13.- I have trouble recognizing a familiar song when played in a different way or by a different performer.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_14 = RadioField("14.- I have never been complimented for my talents as a musical performer.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_15 = RadioField("15.- I often read or search the internet for things related to music.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_16  = RadioField("16.- I often pick certain music to motivate or excite me.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_17 = RadioField("17.- I am not able to sing in harmony when somebody is singing a familiar tune.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_18 = RadioField("18.- I can tell when people sing or play out of time with the beat.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_19 = RadioField("19.- I am able to identify what is special about a given musical piece.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_20 = RadioField("20.- I am able to talk about the emotions that a piece of music evokes for me.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_21 = RadioField("21.- I don’t spend much of my disposable income on music.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_22 = RadioField("22.- I can tell when people sing or play out of tune.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_23 = RadioField("23.- When I sing, I have no idea whether I’m in tune or not.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_24 = RadioField("24.- Music is kind of an addiction for me - I couldn’t live without it.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_25 = RadioField("25.- I don’t like singing in public because I’m afraid that I would sing wrong notes.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_26 = RadioField("26.- When I hear a piece of music I can usually identify its genre.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_27 = RadioField("27.- I would not consider myself a musician.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_28 = RadioField("28.- I keep track of new music that I come across (e.g. new artists or recordings).", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_29 = RadioField("29.- After hearing a new song two or three times, I can usually sing it by myself..", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_30 = RadioField("30.- I only need to hear a new tune once and I can sing it back hours later..", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])
    gms_31 = RadioField("31.- Music can evoke my memories of pastpeople and places.", choices=[(i,i) for i in range(1,8)], validators=[DataRequired()])

    gms_32 = SelectField("Regular Pratice for Years", choices=["0", "1", "2", "3", "4-5", "6-9", "10 or more"], validators=[DataRequired()])
    gms_33 = SelectField("Hours per Day", choices=["0", "0.5", "1", "1.5", "2", "3-4", "5 or more"], validators=[DataRequired()])
    gms_34 = SelectField("Attendance Live Music", choices=["0", "1", "2", "3", "4-6", "7-10", "11 or more"], validators=[DataRequired()])
    gms_35 = SelectField("Music Theory Training", choices=["0", "0.5", "1", "2", "3", "4-6", "7 or more"], validators=[DataRequired()])
    gms_36 = SelectField("Formal Training", choices=["0", "0.5", "1", "2", "3-5", "6-9", "10 or more"], validators=[DataRequired()])
    gms_37 = SelectField("Formal Training", choices=["0", "1", "2", "3", "4", "5", "6 or more"], validators=[DataRequired()])
    gms_38 = SelectField("Formal Training", choices=["0-15 min", "15-30 min", "30-60 min", "60-90 min", "2 hrs", "2-3 hrs", "4 hrs or more"], validators=[DataRequired()])

    gms_39 = StringField("Best Played Instrument", validators=[DataRequired()])

class BEATS_Psychometrics(FlaskForm):
    tipi = FormField(TIPI)
    panas = FormField(PANAS)
    stompr = FormField(STOMPR)
    gms = FormField(GMS)
    current_page = HiddenField(default="1")  # Track the current page
    submit = SubmitField("Submit")






    

