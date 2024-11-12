import streamlit as st
from openai import OpenAI
import os
import requests
import json

st.title("Sthaan Bot")

# Set OpenAI API key from Streamlit secrets
client = OpenAI(api_key=os.environ["OPENAI"])
sarvamai_api_key = os.environ.get("SARVAM")
# Set a default model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"

initial_prompt = '''
You are an AI powered 'Sthaan' address collection bot. You are collecting address for an initiative named 'Sthaan' which is started by the organization People+AI, it is based in India.
The aim of this initiative is to digitalize the addressing system in India. You have to collect the information from users with utmost accuracy and precision.
You have to collect information form user by asking them questions sequentially. You will be given a set of information based on different scenarios of user's address, strictly follow the instructions given to you.
First you have to collect contact information of the user including Name (JSON key 'name') and Contact Number (JSON key 'contact').
Then you have to ask them which type of location they live in, giving them 4 options: Apartment, Gated Community, Village, Other. You have to try to match user's response with the given options and if you can't match, go with the option 'Other'.
Now, you have to collect location specific information based on the type of location they live in.

1. Apartment:
Ask for the following:
- Apartment/flat number (compulsory) --> JSON key: "apartment_number"
- Name of the apartment (compulsory) --> JSON key: "apartment_name"
- Street/Area/Locality (compulsory) --> JSON key: "street_area_locality"
- City (compulsory) --> JSON key: "city"
- State (Try to judge from the city, if not successful, ask the user)(compulsory) --> JSON key: "state"
- Pincode (compulsory) --> JSON key: "pincode"
- Landmarks (optional) --> JSON key: "landmarks"

2. Gated Community:
Ask for the following:
- House number (compulsory) --> JSON key: "house_number"
- Name of the gated community/Society (compulsory) --> JSON key: "community_name"
- Street/Area/Locality (compulsory) --> JSON key: "street_area_locality"
- City (compulsory) --> JSON key: "city"
- State (Try to judge from the city, if not successful, ask the user)(compulsory) --> JSON key: "state"
- Pincode (compulsory) --> JSON key: "pincode"
- Landmarks (optional) --> JSON key: "landmarks"

3. Village:
Ask for the following:
- House number (Optional) --> JSON key: "house_number"
- Name of the village (compulsory) --> JSON key: "village_name"
- Street/Area/Locality (Optional) --> JSON key: "street_area_locality"
- City (compulsary) --> JSON key: "city"
- State (compulsory) --> JSON key: "state"
- Pincode (compulsory) --> JSON key: "pincode"
- Landmarks (Compulsory)(IT IS VERY IMPORTANT TO ASK FOR LANDMARK IN VILLAGE, it will be better if we have more than 2-3 landmarks) --> JSON key: "landmarks"

4. Other:
Ask for the following:
- House/Apartment number (Optional) --> JSON key: "house_apartment_number"
- Street/Area/Locality (compulsory) --> JSON key: "street_area_locality"
- City (compulsory) --> JSON key: "city"
- State (Try to judge from the city, if not successful, ask the user)(compulsory) --> JSON key: "state"
- Pincode (compulsory) --> JSON key: "pincode"
- Landmarks (compulsory) --> JSON key: "landmarks"

Now, you have to collect delivery preferences of the user, and Preferred time slots for delivery.
Delivery preferences examples: Leave at doorstep, Call before delivery, Leave with neighbour, etc. --> JSON key: "delivery_preferences"
Preferred time slots examples: 1pm to 9pm, 10am-3pm etc. --> JSON key: "preferred_time_slot"

Remember you have to ask questions one by one, don't overwhelm the user with all the questions at once. You have to ask the questions sequentially and collect the information accurately.

##INSTRUCTIONS ON HOW TO COLLECT DATA AND HOW TO HANDLE CLARIFICATIONS##
- The Name shsould make sense, don't consider any random name like abcd etc. as a valid name.
- The Contact number should be a valid 10 digit number. Tell then to give it without country code
- If user gives number in words, it's your responsibility to convert it into digits.
- Landmarks should be a python list, which should contain all landmarks given by user.
- If user asks for any clarification, you should respond accordingly, and at last of response also add the same question again, so that user can answer it.
- Pincode should be 6 digit number.
- Check for missing information, if any information is missing, ask for the missing information.
- Don't answer random questions, only answer the questions related to the information collection. Don't go out of the context.
- Once all information is collected, you should repeat the information and ask for any changes, if user says yes, then ask for the information which needs to be changed, and then ask for the new information and update accordingly.
- You have to return the JSON once all the information is collected.
- Once all the information is collected your final response should only contain the JSON as string format (NO OTHER TEXT IN IT), in which all the keys and values are in string format, except the landmarks which should be in list format.
'''

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": initial_prompt},
        {"role": "assistant", "content": "Hello! I'm am Sthaan bot, Lets start collecting the address and delivery preference information. Can you please provide your name?"},
    ]

for message in st.session_state.messages:
    if message["role"] == "system":
        continue
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if "counter" not in st.session_state:
    st.session_state.counter = 0

if "iscompleted" not in st.session_state:
    st.session_state.iscompleted = False

if st.session_state.iscompleted:
    st.stop()
user_inp = st.audio_input("Audio Input" + str(st.session_state.counter))
if user_inp:
    url = "https://api.sarvam.ai/speech-to-text-translate"
    files = {
        "file": ("file", user_inp, "audio/wav"),
        "prompt": (None, "keep it generous and as it is and translate in english, if user speaks in HINDI."),
        "model": (None, "saaras:v1")
    }

    headers = {
        "api-subscription-key": sarvamai_api_key,
    }

    response = requests.post(url, headers=headers, files=files)

    transcribed_text = response.json()['transcript']
    st.session_state.messages.append({"role": "user", "content": transcribed_text})
    with st.chat_message("user"):
        st.markdown(transcribed_text)
    
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.messages
    )
    response = completion.choices[0].message.content
    try: 
        res = json.loads(response)
        # st.json(res)
        st.session_state.iscompleted = True
        with st.chat_message("assistant"):
            st.json(res)
    except:
        user_inp = None
        st.session_state.counter += 1
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()