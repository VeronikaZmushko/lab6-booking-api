from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, time, datetime
from enum import Enum

app = FastAPI(
    title="АС БАФ: Система бронирования аудиторного фонда",
    version="1.0.0",
    description="REST API для управления заявками на бронирование аудиторий",
)

# ---------- DTO (модели данных) на основе ТЗ ----------

class BookingStatus(str, Enum):
    new = "Новая"
    approved = "Одобрена"
    rejected = "Отклонена"

class BookingRequestBase(BaseModel):
    applicant: str = Field(..., description="Заявитель (кафедра/сотрудник)")
    classroom: str = Field(..., description="Требуемая аудитория")
    booking_date: date = Field(..., description="Дата бронирования")
    time_start: time = Field(..., description="Время начала")
    time_end: time = Field(..., description="Время окончания")
    purpose: str = Field(..., description="Цель занятия или мероприятия")
    status: BookingStatus = Field(default=BookingStatus.new, description="Статус заявки")
    decision: Optional[str] = Field(None, description="Результат рассмотрения (подтверждение/отказ)")

class BookingRequestCreate(BookingRequestBase):
    pass

class BookingRequest(BookingRequestBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.now, description="Дата подачи заявки")

# ---------- In-Memory хранилище ----------

bookings_db: dict[int, BookingRequest] = {}
_next_id = 1

# ---------- Эндпоинты ----------

@app.get("/api/v1/bookings/", response_model=List[BookingRequest], status_code=status.HTTP_200_OK,
         summary="Получить список всех заявок",
         responses={
             200: {"description": "Успешный возврат списка заявок"},
             500: {"description": "Внутренняя ошибка сервера"}
         })
def list_bookings():
    """Возвращает список всех заявок на бронирование."""
    return list(bookings_db.values())

@app.get("/api/v1/bookings/{booking_id}", response_model=BookingRequest, status_code=status.HTTP_200_OK,
         summary="Получить заявку по id",
         responses={
             200: {"description": "Заявка найдена"},
             404: {"description": "Заявка с указанным id не найдена"}
         })
def get_booking(booking_id: int):
    """Возвращает детальную информацию о заявке по ее идентификатору."""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    return bookings_db[booking_id]

@app.post("/api/v1/bookings/", response_model=BookingRequest, status_code=status.HTTP_201_CREATED,
          summary="Создать новую заявку на бронирование",
          responses={
              201: {"description": "Заявка успешно создана"},
              400: {"description": "Некорректные входные данные (ошибка валидации)"}
          })
def create_booking(payload: BookingRequestCreate):
    """Создает новую заявку на бронирование аудитории."""
    global _next_id
    new_booking = BookingRequest(id=_next_id, **payload.model_dump())
    bookings_db[_next_id] = new_booking
    _next_id += 1
    return new_booking

@app.delete("/api/v1/bookings/{booking_id}", status_code=status.HTTP_200_OK,
            summary="Удалить заявку",
            responses={
                200: {"description": "Заявка успешно удалена"},
                404: {"description": "Заявка с указанным id не найдена"}
            })
def delete_booking(booking_id: int):
    """Удаляет заявку по ее идентификатору."""
    if booking_id not in bookings_db:
        raise HTTPException(status_code=404, detail="Заявка не найдена")
    del bookings_db[booking_id]
    return {"message": f"Заявка {booking_id} удалена"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)