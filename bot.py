from collections import UserDict
from datetime import datetime, timedelta
import pickle
import re


class Field:
    """Базовий клас для полів запису."""
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Клас для зберігання імені контакту."""
    def __init__(self, value):
        if not isinstance(value, str) or not value.strip():
            raise ValueError("Name is required")
        super().__init__(value.strip())


class Phone(Field):
    """Клас для зберігання телефонного номера (10 цифр)."""
    def __init__(self, value):
        if not isinstance(value, str):
            raise ValueError("Phone number must be a string")
        # Видаляємо всі символи крім цифр
        cleaned = re.sub(r"\D", "", value)
        if not self._is_valid_phone(cleaned):
            raise ValueError("Phone number must contain exactly 10 digits")
        super().__init__(cleaned)

    @staticmethod
    def _is_valid_phone(value):
        return (isinstance(value, str) and
                re.fullmatch(r"\d{10}", value) is not None)


class Birthday(Field):
    """Клас для зберігання дня народження у форматі DD.MM.YYYY."""
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use DD.MM.YYYY. Error: {e}")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:
    """Клас для зберігання інформації про контакт."""
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):
        phone_obj = self.find_phone(phone)
        if phone_obj is None:
            raise ValueError("Phone not found")
        self.phones.remove(phone_obj)

    def edit_phone(self, old_phone, new_phone):
        phone_obj = self.find_phone(old_phone)
        if phone_obj is None:
            raise ValueError("Phone not found")
        phone_obj.value = Phone(new_phone).value

    def find_phone(self, phone):
        # Видаляємо всі символи крім цифр для порівняння
        cleaned = re.sub(r"\D", "", phone)
        for phone_obj in self.phones:
            if phone_obj.value == cleaned:
                return phone_obj
        return None

    def add_birthday(self, birthday):
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones_str = '; '.join(p.value for p in self.phones)
        birthday_str = (
            f", birthday: {self.birthday}" if self.birthday else ""
        )
        return (
            f"Contact name: {self.name.value}, "
            f"phones: {phones_str}{birthday_str}"
        )


class AddressBook(UserDict):
    """Клас для зберігання та управління записами контактів."""
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        today = datetime.today().date()
        upcoming_birthdays = []

        for record in self.data.values():
            if record.birthday is None:
                continue

            birthday_date = record.birthday.value.date()

            try:
                birthday_this_year = birthday_date.replace(
                    year=today.year
                )
            except ValueError:
                birthday_this_year = birthday_date.replace(
                    year=today.year, day=28
                )

            if birthday_this_year < today:
                try:
                    birthday_this_year = birthday_date.replace(
                        year=today.year + 1
                    )
                except ValueError:
                    birthday_this_year = birthday_date.replace(
                        year=today.year + 1, day=28
                    )

            days_until_birthday = (birthday_this_year - today).days

            if 0 <= days_until_birthday <= 7:
                congratulation_date = birthday_this_year

                if birthday_this_year.weekday() == 5:
                    congratulation_date = (
                        birthday_this_year + timedelta(days=2)
                    )
                elif birthday_this_year.weekday() == 6:
                    congratulation_date = (
                        birthday_this_year + timedelta(days=1)
                    )

                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": (
                        congratulation_date.strftime("%d.%m.%Y")
                    )
                })

        return upcoming_birthdays


def save_data(book, filename="addressbook.pkl"):
    """Зберігає адресну книгу у файл за допомогою pickle."""
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    """Завантажує адресну книгу з файлу. Повертає нову книгу, якщо файл не знайдено."""
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def input_error(func):
    """Декоратор для обробки помилок введення."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return str(e)
        except IndexError:
            return "Not enough arguments provided."
        except KeyError:
            return "Contact not found."
        except Exception as e:
            return f"An error occurred: {str(e)}"
    return inner


def parse_input(user_input):
    """Парсинг введеної команди користувача."""
    parts = user_input.split()
    command = parts[0].strip().lower() if parts else ""
    args = parts[1:] if len(parts) > 1 else []
    return command, args


@input_error
def add_contact(args, book: AddressBook):
    """Додає новий контакт або телефон до існуючого контакту."""
    if len(args) < 2:
        return "Please provide name and phone number."

    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args, book: AddressBook):
    """Змінює телефонний номер контакту."""
    if len(args) < 3:
        return "Please provide name, old phone and new phone."

    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact {name} not found."

    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    """Показує телефонні номери контакту."""
    if len(args) < 1:
        return "Please provide contact name."

    name = args[0]
    record = book.find(name)
    if record is None:
        return f"Contact {name} not found."

    if not record.phones:
        return f"No phone numbers for {name}."

    phones = ', '.join(p.value for p in record.phones)
    return f"{name}: {phones}"


@input_error
def show_all(args, book: AddressBook):
    """Показує всі контакти в адресній книзі."""
    if not book.data:
        return "No contacts in address book."

    result = []
    for record in book.data.values():
        result.append(str(record))
    return '\n'.join(result)


@input_error
def add_birthday(args, book: AddressBook):
    """Додає день народження до контакту."""
    if len(args) < 2:
        return "Please provide name and birthday (DD.MM.YYYY)."

    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        return f"Contact {name} not found."

    record.add_birthday(birthday)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    """Показує день народження контакту."""
    if len(args) < 1:
        return "Please provide contact name."

    name = args[0]
    record = book.find(name)
    if record is None:
        return f"Contact {name} not found."

    if record.birthday is None:
        return f"No birthday set for {name}."

    return f"{name}: {record.birthday}"


@input_error
def birthdays(args, book: AddressBook):
    """Показує дні народження на наступний тиждень."""
    upcoming = book.get_upcoming_birthdays()

    if not upcoming:
        return "No upcoming birthdays in the next week."

    result = ["Upcoming birthdays:"]
    for item in upcoming:
        result.append(
            f"  {item['name']}: {item['congratulation_date']}"
        )

    return '\n'.join(result)


def get_help():
    """Повертає відформатований список усіх доступних команд."""
    commands = [
        ("hello", "Привітання від бота."),
        ("add <name> <phone>", "Додати контакт або телефон до існуючого. Телефон — 10 цифр."),
        ("change <name> <old_phone> <new_phone>", "Змінити номер телефону контакту."),
        ("phone <name>", "Показати всі телефони контакту."),
        ("all", "Показати всі контакти в адресній книзі."),
        ("add-birthday <name> <DD.MM.YYYY>", "Додати день народження контакту."),
        ("show-birthday <name>", "Показати день народження контакту."),
        ("birthdays", "Показати дні народження на найближчий тиждень."),
        ("help", "Показати цей список команд."),
        ("close / exit", "Зберегти дані та вийти з програми."),
    ]
    width = max(len(cmd) for cmd, _ in commands) + 2
    lines = ["Available commands:", ""]
    for cmd, desc in commands:
        lines.append(f"  {cmd:<{width}} {desc}")
    return "\n".join(lines)


def main():
    """Головна функція програми."""
    book = load_data()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")

        elif command == "help":
            print(get_help())

        elif command == "add":
            print(add_contact(args, book))

        elif command == "change":
            print(change_contact(args, book))

        elif command == "phone":
            print(show_phone(args, book))

        elif command == "all":
            print(show_all(args, book))

        elif command == "add-birthday":
            print(add_birthday(args, book))

        elif command == "show-birthday":
            print(show_birthday(args, book))

        elif command == "birthdays":
            print(birthdays(args, book))

        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()
