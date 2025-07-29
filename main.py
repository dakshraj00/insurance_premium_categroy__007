from fastapi import FastAPI, HTTPException,Path,Query
import json
from fastapi.responses import JSONResponse
from pydantic import BaseModel,Field,computed_field
from typing import Annotated,Literal,Optional
app = FastAPI()
class Patient(BaseModel):

    id:Annotated[str,Field(...,description='id of the patients',examples=['P001'])]
    name:Annotated[str,Field(...,description='name fo the patient')]

    city:Annotated[str,Field(...,description="city where you live")]
    age:Annotated[int,Field(...,description="current age of yours",gt=0,lt=60)]
    gender:Annotated[Literal['male','female','others'],Field(...,description="gender of yours")]
    height:Annotated[float,Field(...,description="current height",gt=0)]
    weight:Annotated[float,Field(...,description="weight of yours",gt=0)]

    @computed_field
    @property
    def bmi(self)->float:
        bmi = round(self.weight / (self.height**2), 2)
        return bmi
    
    @computed_field
    @property
    def verdict(self)->str:
        if self.bmi>25:
            return "overweight"
        elif self.bmi<18.5:
            return "underweight"
        elif self.bmi>30:
            return "Mote saaand"
        else :
            return "Congratulation you are a fit person"

class PatientUpdate(BaseModel):
    id:Annotated[Optional[str],Field(default=None,description='id of the patients',examples=['P001'])]
    name:Annotated[Optional[str],Field(default=None,description='name fo the patient')]

    city:Annotated[Optional[str],Field(default=None,description="city where you live")]
    age:Annotated[Optional[int],Field(default=None,description="current age of yours",gt=0,lt=60)]
    gender:Annotated[Optional[Literal['male','female','others']],Field(default=None,description="gender of yours")]
    height:Annotated[Optional[float],Field(default=None,description="current height",gt=0)]
    weight:Annotated[Optional[float],Field(default=None,description="weight of yours",gt=0)]
    

def load_data():
    with open("patients.json", 'r') as f:
        return json.load(f)
    
def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)

@app.get("/")
def hello():
    return {"message": "Patient Data API"}

@app.get("/view")
def view_all_patients():
    return load_data()

@app.get("/patient/{patient_id}")# this ... =required
def view_patient(patient_id: str=Path(...,description="id of the patients in the db",example='P001')):
    data = load_data()
    if patient_id in data:
        return data[patient_id]
    else:
        raise HTTPException(status_code=404, detail=f"Patient '{patient_id}' not found")

@app.get("/sort")
def sort_patient(sortby:str=Query(...,description="select the height ,weigh,bmi",),
                 order:str=Query('asc',description='select the order asc,desc')):
    valid_fields=['height','weight','bmi']
    if sortby not in valid_fields:
        raise HTTPException(status_code=404,detail=f'select form valid fields{valid_fields}')
    if order not in ["asc","desc"]:
        raise HTTPException(status_code=404,detail=f'selct valid order asc ,desc')
    data=load_data()
    sort_order = True if order == 'desc' else False
    sorted_data=data(data.values(),key=lambda x:x.get(sortby,0),reversed=sort_order)

    return sorted_data

@app.post("/create")
def create_patient(pati:Patient):

    # 1st load data
    data=load_data()

    # 2nd check if exist
    if pati.id in data:
        raise HTTPException(status_code=400,detail="patient already exist")

    # 3rd new patient in the database
    else:
        data[pati.id]=pati.model_dump(exclude={'id'})

    # 4th save the data
    save_data(data)

    return JSONResponse(status_code=201,content={"message":'patient created succesfully'})

@app.put("/edit/{patient_id}")
def update_patient(patient_id:str,patient_update:PatientUpdate):

    data=load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404,detail="patient not found")

    existing_patient_info=data[patient_id]
    
    updated_patient_info=patient_update.model_dump(exclude_unset=True)

    for key ,value in updated_patient_info.items():
        existing_patient_info[key]=value
    
    # existing_patient_info->pydantic to update bmi and verdict
    existing_patient_info['id']=patient_id
    patient_pydantic_obj=Patient(**existing_patient_info)

    # pydantic->dict
    existing_patient_info=patient_pydantic_obj.model_dump(exclude='id')
    # add this data 

    data[patient_id]=existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200,content={'message':"successfully edited"})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data=load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404,detail="error not found")
    
    del data[patient_id]

    save_data(data)

    return JSONResponse(status_code=200,content="deleted succesfully!!")