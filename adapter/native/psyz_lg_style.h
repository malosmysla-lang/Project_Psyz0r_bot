// Шафт: меняем только игровые команды. Координат врага и подмены попаданий здесь нет.
typedef struct {int last;float angle[2],bias[2];} PsyzLGSmooth;
static float Psyz_LGWrap(float angle){while(angle>180)angle-=360;while(angle< -180)angle+=360;return angle;}
static void Psyz_LGSmoothReset(PsyzLGSmooth *s){memset(s,0,sizeof(*s));}
static void Psyz_LGSmoothCommand(PsyzLGSmooth *s,int angles[3],const float current[2],int now,float error_degrees,float rate,const float seed[2]){
    int dt=now-s->last;
    // Новая очередь или сброс часов: начинаем от реального взгляда бота,
    // а не переносим прицел из предыдущего боя или прошлой жизни.
    if(!s->last || dt<=0 || dt>150){
        dt=25;
        for(int a=0;a<2;a++){s->angle[a]=current[a];s->bias[a]=seed[a];}
    }
    s->last=now;
    // Небольшое запаздывание сопровождения заменяет прежнюю колебательную тряску.
    // Ошибка постоянна внутри очереди: это неточность, а не дрожащая синусоида.
    float step[2],norm=0,blend=dt/(50.f+dt);
    for(int a=0;a<2;a++){
        float desired=angles[a]*360.f/65536.f+s->bias[a]*error_degrees;
        step[a]=Psyz_LGWrap(desired-s->angle[a])*blend;norm+=step[a]*step[a];
    }
    // Ограничиваем суммарный поворот по двум осям: нельзя мгновенно развернуться на 180°.
    norm=sqrtf(norm);float maximum=rate*dt/1000.f;
    float scale=norm>maximum && norm>0?maximum/norm:1;
    for(int a=0;a<2;a++){s->angle[a]=Psyz_LGWrap(s->angle[a]+step[a]*scale);angles[a]=(int)(s->angle[a]*65536.f/360.f);}
}
typedef struct {int last,sign[2],since[2];} PsyzLGFeet;
static void Psyz_LGFeetReset(PsyzLGFeet *s){memset(s,0,sizeof(*s));}
static void Psyz_LGFeetCommand(PsyzLGFeet *s,signed char *forward,signed char *right,int now){
    signed char *axes[2]={forward,right};
    // Направление берём у штатного боевого AI: он уже проверяет проход и препятствия.
    // Не сохраняем старый вектор после его отказа — иначе можно продолжить идти в стену.
    if(!s->last || now<=s->last || now-s->last>150)Psyz_LGFeetReset(s);
    s->last=now;
    for(int a=0;a<2;a++){
        int value=*axes[a],sign=value>0?1:value<0?-1:0;
        if(!sign){s->sign[a]=0;s->since[a]=now;continue;}
        if(sign!=s->sign[a]){s->sign[a]=sign;s->since[a]=now;}
        // При смене стрейфа усиливаем команду плавно за 150 мс.
        // Это не предикт ракеты и не принудительная пауза под чужой выстрел.
        float ramp=fminf(1.f,(now-s->since[a])/150.f);
        *axes[a]=(signed char)(value*(.65f+.35f*ramp));
    }
}
