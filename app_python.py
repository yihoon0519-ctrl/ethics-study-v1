import json, random, re
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='통합사회2 윤리 암기 학습', page_icon='📚', layout='wide')
HTML_PATH = Path(__file__).with_name('study.html')

@st.cache_data
def load_data():
    html = HTML_PATH.read_text(encoding='utf-8')
    m = re.search(r'const DATA=(\{.*?\});let group=', html, re.S)
    if not m:
        raise ValueError('study.html에서 학습 DATA를 찾지 못했습니다.')
    return html, json.loads(m.group(1))

html, DATA = load_data()

def build_bank(names):
    bank=[]
    for name in names:
        thinker=name.replace(' OX','')
        for text, answer in DATA['ox'][name]:
            bank.append({'thinker':thinker,'text':text,'answer':answer})
    return bank

def clear_quiz():
    for k in ['questions','idx','correct','wrong','results','answered','choice','finished','retry']:
        st.session_state.pop(k, None)

def start_quiz(names, count):
    bank=build_bank(names)
    random.shuffle(bank)
    st.session_state.questions=bank[:min(count,len(bank))]
    st.session_state.idx=0; st.session_state.correct=0
    st.session_state.wrong=[]; st.session_state.results=[]
    st.session_state.answered=False; st.session_state.choice=None
    st.session_state.finished=False; st.session_state.retry=False

def answer(choice):
    q=st.session_state.questions[st.session_state.idx]
    ok=(choice==q['answer'])
    st.session_state.choice=choice; st.session_state.answered=True
    if ok: st.session_state.correct += 1
    else: st.session_state.wrong.append(q.copy())
    st.session_state.results.append({'thinker':q['thinker'],'correct':ok})

def next_q():
    st.session_state.idx += 1
    st.session_state.answered=False; st.session_state.choice=None
    if st.session_state.idx >= len(st.session_state.questions):
        st.session_state.finished=True

def retry_wrong():
    qs=[q.copy() for q in st.session_state.wrong]
    random.shuffle(qs)
    st.session_state.questions=qs; st.session_state.idx=0
    st.session_state.correct=0; st.session_state.wrong=[]; st.session_state.results=[]
    st.session_state.answered=False; st.session_state.choice=None
    st.session_state.finished=False; st.session_state.retry=True

def result_screen():
    total=len(st.session_state.questions); correct=st.session_state.correct
    rate=round(correct/total*100) if total else 0
    st.subheader('📊 학습 결과')
    a,b,c=st.columns(3)
    a.metric('맞힌 문제',f'{correct} / {total}')
    b.metric('정답률',f'{rate}%')
    c.metric('오답',f'{len(st.session_state.wrong)}문제')
    stats={}
    for r in st.session_state.results:
        s=stats.setdefault(r['thinker'],{'correct':0,'total':0})
        s['total']+=1
        if r['correct']: s['correct']+=1
    if stats:
        st.markdown('#### 사상가별 정답률')
        weakest=None
        for name,s in stats.items():
            r=round(s['correct']/s['total']*100)
            st.write(f"**{name}**: {s['correct']}/{s['total']} ({r}%)")
            st.progress(r/100)
            if weakest is None or r < weakest[1]: weakest=(name,r)
        st.info(f'📌 가장 복습이 필요한 영역: **{weakest[0]} ({weakest[1]}%)**')
    if st.session_state.wrong:
        st.markdown('#### 틀린 문제')
        for i,q in enumerate(st.session_state.wrong,1):
            st.write(f"{i}. [{q['thinker']}] {q['text']} → **{q['answer']}**")
        if st.button('🔁 틀린 문제만 다시 풀기', use_container_width=True):
            retry_wrong(); st.rerun()
    else:
        st.success('🎉 틀린 문제가 없습니다!')
    if st.button('🆕 새 테스트 시작', use_container_width=True):
        clear_quiz(); st.rerun()

st.title('📚 통합사회2 윤리 암기 학습')
tab1,tab2=st.tabs(['📖 1·2·3단계 암기','🐍 Python 실전 OX'])
with tab1:
    st.caption('기존 프린트 원문과 1·2·3단계 암기 기능을 그대로 유지했습니다.')
    components.html(html,height=2200,scrolling=True)
with tab2:
    st.subheader('🐍 Python 실전 OX 테스트')
    st.caption('문제 선택·무작위 출제·정답 판정·점수 계산·오답 저장·사상가별 분석을 Python이 처리합니다.')
    if 'questions' not in st.session_state:
        names=list(DATA['ox'].keys())
        selected=st.multiselect('출제 범위',names,default=names)
        available=len(build_bank(selected)) if selected else 0
        if available:
            count=st.number_input('문제 수',1,available,min(20,available),1)
            if st.button('▶️ 테스트 시작',type='primary',use_container_width=True):
                start_quiz(selected,int(count)); st.rerun()
        else: st.warning('출제할 사상가를 한 명 이상 선택하세요.')
    elif st.session_state.finished:
        result_screen()
    else:
        qs=st.session_state.questions; i=st.session_state.idx; q=qs[i]
        suffix=' · 오답 재도전' if st.session_state.retry else ''
        st.write(f'**{i+1} / {len(qs)}{suffix}**'); st.progress((i+1)/len(qs))
        st.markdown(f"### {q['text']}"); st.caption(f"사상가: {q['thinker']}")
        if not st.session_state.answered:
            c1,c2=st.columns(2)
            with c1:
                if st.button('⭕ O',use_container_width=True): answer('O'); st.rerun()
            with c2:
                if st.button('❌ X',use_container_width=True): answer('X'); st.rerun()
        else:
            if st.session_state.choice==q['answer']: st.success(f"정답입니다! 정답: {q['answer']}")
            else: st.error(f"틀렸습니다. 내가 선택한 답: {st.session_state.choice} / 정답: {q['answer']}")
            label='결과 보기' if i==len(qs)-1 else '다음 문제 →'
            if st.button(label,type='primary',use_container_width=True): next_q(); st.rerun()
        if st.button('테스트 종료하고 처음으로',use_container_width=True): clear_quiz(); st.rerun()
