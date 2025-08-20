from collections import UserDict
import datetime

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            return "Enter the argument for the command"
        except KeyError:
            return "Contact not found."
        except IndexError:
            return "Enter the argument for the command"
    return inner

def parse_input(user_input: str) -> tuple[str, list[str]]:
    parts = user_input.strip().split()
    cmd = parts[0].lower()
    args = parts[1:]
    return cmd, args

# ===== Fields =====
class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)

class Name(Field):
    pass

class Phone(Field):
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone must be a 10-digit string")
        super().__init__(value)

class Birthday(Field):
    def __init__(self, value):
        try:
            _ = datetime.datetime.strptime(value, "%d.%m.%Y").date()
        except Exception:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        self.value = value

# ===== Record =====
class Record:
    def __init__(self, name: str):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, new_phone: str):
        if self.find_phone(new_phone):
            raise ValueError(f"Phone number {new_phone} already exists for {self.name.value}")
        phone = Phone(new_phone)
        self.phones.append(phone)

    def remove_phone(self, rem_phone: str):
        phone_obj = self.find_phone(rem_phone)
        if phone_obj:
            self.phones.remove(phone_obj)
        else:
            raise ValueError(f"Phone number {rem_phone} not found")

    def edit_phone(self, old: str, new: str):
        phone_obj = self.find_phone(old)
        if not phone_obj:
            raise ValueError(f"Phone number {old} not found")
        self.add_phone(new)
        self.remove_phone(old)

    def find_phone(self, phone_str: str):
        for ph in self.phones:
            if ph.value == phone_str:
                return ph
        return None

    def add_birthday(self, bday_value: str):
        if self.birthday is not None:
            raise ValueError("Birthday already set for this contact")
        bday = Birthday(bday_value)
        self.birthday = bday

    def __str__(self):
        phones = '; '.join(p.value for p in self.phones) if self.phones else "no phones"
        bday = self.birthday.value if self.birthday else "no birthday"  # Виправлено
        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {bday}"

# ===== AddressBook =====
class AddressBook(UserDict):
    def add_record(self, record: Record):
        key = record.name.value
        self.data[key] = record

    def find(self, name_str: str):
        return self.data.get(name_str)

    def delete(self, name_str: str):
        self.data.pop(name_str, None)

    def __str__(self):
        if not self.data:
            return "Address book is empty."
        lines = [str(rec) for rec in self.data.values()]
        return "\n".join(lines)

    def get_upcoming_birthdays(self) -> list:
        today = datetime.date.today()
        end_date = today + datetime.timedelta(days=6)
        result = []

        for rec in self.data.values():
            if rec.birthday is None:
                continue

            bday_str = rec.birthday.value
            bday_dt = datetime.datetime.strptime(bday_str, "%d.%m.%Y").date()

            year = today.year
            try:
                candidate = datetime.date(year, bday_dt.month, bday_dt.day)
            except ValueError:
                continue

            if candidate < today:
                candidate = datetime.date(year + 1, bday_dt.month, bday_dt.day)


            #if it's a weekend, we move it to Monday 
            weekday = candidate.weekday()  # Mon=0 ... Sun=6
            shifted = candidate
            if weekday == 5:  # Saturday -> +2
                shifted = candidate + datetime.timedelta(days=2)
            elif weekday == 6:  # Sunday -> +1
                shifted = candidate + datetime.timedelta(days=1)

            if today <= shifted <= end_date:
                result.append({
                    "name": rec.name.value,
                    "birthday": shifted.strftime("%d.%m.%Y")
                })

        return result

# ===== Command handlers =====
@input_error
def add_contact(args: list[str], book: AddressBook) -> str:
    name, phone = args
    rec = book.find(name)
    if rec is None:
        rec = Record(name)
        if phone:
            rec.add_phone(phone)
        book.add_record(rec)
        return "Contact added."
    else:
        if phone:
            rec.add_phone(phone)
            return "Phone added to existing contact."
        return "Contact already exists."


@input_error
def change_contact(args: list[str], book: AddressBook) -> str:
    name, old_phone, new_phone = args
    rec = book.find(name)
    if rec is None:
        raise KeyError
    rec.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args: list[str], book: AddressBook) -> str:
    name = args[0]
    rec = book.find(name)
    if rec is None:
        raise KeyError
    phones = ', '.join(p.value for p in rec.phones) if rec.phones else "No phones"
    return f"Contact for {name}: {phones}"

def show_all(book: AddressBook) -> str:
    if not book.data:
        return "No contacts found."
    return "\n".join(f"{name}: {', '.join(p.value for p in rec.phones) if rec.phones else 'no phones'}; birthday: {rec.birthday.value if rec.birthday else 'no birthday'}"  # Виправлено
                     for name, rec in book.data.items())

# ============    ================
@input_error
def add_birthday(args, book: AddressBook):
    name, bday = args
    rec = book.find(name)
    if rec is None:
        raise KeyError
    rec.add_birthday(bday)
    return "Birthday added."

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    rec = book.find(name)
    if rec is None:
        raise KeyError
    if rec.birthday:
        return f"{name}: {rec.birthday.value}"
    else:
        return f"Birthday for {name} not set."

@input_error
def birthdays(args, book: AddressBook):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No upcoming birthdays."
    lines = [f"{d['name']}: {d['birthday']}" for d in upcoming]
    return "\n".join(lines)

# ===== CLI =====
def main():
    book = AddressBook()
    print("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ").strip()

        if not user_input:
            print("Please enter a command.")
            continue

        command, args = parse_input(user_input)

        if command in ["close", "exit"]:
            print("Good bye!")
            break

        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(show_phone(args, book))
        elif command == "all":
            print(show_all(book))
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