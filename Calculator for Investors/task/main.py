import csv
from sqlalchemy import Column, String, Float, create_engine, ForeignKey, desc, func
from sqlalchemy.orm import declarative_base, Session, relationship, column_property
from os.path import exists

Base = declarative_base()


class Company(Base):
    __tablename__ = "companies"

    ticker = Column(String, primary_key=True)
    name = Column(String)
    sector = Column(String)
    financial = relationship("Financial", back_populates="company", uselist=False)

    def __repr__(self):
        return f"{self.ticker} {self.name}\n{self.financial}"


class Financial(Base):
    __tablename__ = "financial"

    ticker = Column(String, ForeignKey("companies.ticker"), primary_key=True)
    ebitda = Column(Float)
    sales = Column(Float)
    net_profit = Column(Float)
    market_price = Column(Float)
    net_debt = Column(Float)
    assets = Column(Float)
    equity = Column(Float)
    cash_equivalents = Column(Float)
    liabilities = Column(Float)
    company = relationship("Company", back_populates="financial")
    pe = column_property(func.round(market_price / net_profit, 2))
    ps = column_property(func.round(market_price / sales, 2))
    pb = column_property(func.round(market_price / assets, 2))
    ndebita = column_property(func.round(net_debt / ebitda, 2))
    roe = column_property(func.round(net_profit / equity, 2))
    roa = column_property(func.round(net_profit / assets, 2))
    la = column_property(func.round(liabilities / assets, 2))

    def get_ndebita(self):
        return round(self.net_debt / self.ebitda, 2) if self.net_debt and self.ebitda else None

    def get_roe(self):
        return round(self.net_profit / self.equity, 2) if self.net_profit and self.equity else None

    def get_roa(self):
        return round(self.net_profit / self.assets, 2) if self.net_profit and self.assets else None

    def __repr__(self):
        return f"P/E = {self.pe}\n" \
               f"P/S = {self.ps}\n" \
               f"P/B = {self.pb}\n" \
               f"ND/EBITDA = {self.ndebita}\n" \
               f"ROE = {self.roe}\n" \
               f"ROA = {self.roa}\n" \
               f"L/A = {self.la}"


def update_fields(obj: object, fields: dict):
    for k, v in fields.items():
        obj.__setattr__(k, None if v == '' else v)


def create_object(base, fields: dict):
    obj = base()
    update_fields(obj, fields)
    return obj


def find_company(session) -> Company:
    name = input("Enter company name:\n")
    companies = session.query(Company).filter(Company.name.ilike(f"%{name}%")).all()
    if len(companies) == 0:
        return None
    for i, company in enumerate(companies):
        print(f"{i} {company.name}")
    company_number = input("Enter company number:\n")
    return companies[int(company_number)]


def crud_menu(session):
    company_fields = {"ticker": "Enter ticker (in the format 'MOON'):",
                      "name": "Enter company (in the format 'Moon Corp'):",
                      "sector": "Enter industries (in the format 'Technology'):"}
    financial_fields = {"ebitda": "Enter ebitda (in the format '987654321'):",
                        "sales": "Enter sales (in the format '987654321'):",
                        "net_profit": "Enter net profit (in the format '987654321'):",
                        "market_price": "Enter market price (in the format '987654321'):",
                        "net_debt": "Enter net debt (in the format '987654321'):",
                        "assets": "Enter assets (in the format '987654321'):",
                        "equity": "Enter equity (in the format '987654321'):",
                        "cash_equivalents": "Enter cash equivalents (in the format '987654321'):",
                        "liabilities": "Enter liabilities (in the format '987654321'):"}
    print("CRUD MENU")
    print("0 Back")
    print("1 Create a company")
    print("2 Read a company")
    print("3 Update a company")
    print("4 Delete a company")
    print("5 List all companies")
    print("Enter an option:")
    option = input()
    if option == '0':
        return
    elif option == '1':
        company = Company()
        for field, prompt in company_fields.items():
            value = input(prompt + "\n")
            company.__setattr__(field, None if value == '' else value)
        financial = Financial(company.ticker)
        for field, prompt in financial_fields.items():
            value = input(prompt + "\n")
            financial.__setattr__(field, None if value == '' else float(value))
        company.financial = financial
        session.add(company)
        session.commit()
        print("Company created successfully!")
    elif option == '2':
        company = find_company(session)
        if company is None:
            print("Company not found!")
        else:
            print(company)
    elif option == '3':
        company = find_company(session)
        if company is None:
            print("Company not found!")
        else:
            for field, prompt in financial_fields.items():
                value = input(prompt + "\n")
                company.financial.__setattr__(field, None if value == '' else float(value))
            session.commit()
            print("Company updated successfully!")
    elif option == '4':
        company = find_company(session)
        if company is None:
            print("Company not found!")
        else:
            session.delete(company)
            session.commit()
            print("Company deleted successfully!")
    elif option == '5':
        print("COMPANY LIST")
        for company in session.query(Company).order_by(Company.ticker).all():
            print(f"{company.ticker} {company.name} {company.sector}")
    else:
        print("Invalid option!")


def top_ten_menu(session):
    print("TOP TEN MENU")
    print("0 Back")
    print("1 List by ND/EBITDA")
    print("2 List by ROE")
    print("3 List by ROA")
    print("Enter an option:")
    option = input()
    if option == '0':
        return
    elif option in ['1', '2', '3']:
        financials = session.query(Financial)
        if option == '1':
            financials = financials.order_by(desc(Financial.ndebita)).limit(10)
            print("TICKER ND/EBITDA")
            for financial in financials.all():
                print(f"{financial.ticker} {financial.ndebita}")
        elif option == '2':
            financials = financials.order_by(desc(Financial.roe)).limit(10)
            print("TICKER ROE")
            for financial in financials.all():
                print(f"{financial.ticker} {financial.roe}")
        elif option == '3':
            financials = financials.order_by(desc(Financial.roa)).limit(10)
            print("TICKER ROA")
            for financial in financials.all():
                print(f"{financial.ticker} {financial.roa}")
    else:
        print("Invalid option!")


def main_menu(session):
    while True:
        print("MAIN MENU")
        print("0 Exit")
        print("1 CRUD operations")
        print("2 Show top ten companies by criteria")
        print("Enter an option:")
        option = input()
        if option == '0':
            print("Have a nice day!")
            return
        elif option == '1':
            crud_menu(session)
        elif option == '2':
            top_ten_menu(session)
        else:
            print("Invalid option!")


def create_database(engine):
    companies = csv.DictReader(open('test/companies.csv'))
    financials = csv.DictReader(open('test/financial.csv'))

    Base.metadata.create_all(engine)
    with Session(engine) as session:
        all_financials = dict()
        for financial in financials:
            all_financials[financial['ticker']] = create_object(Financial, financial)
        for company in companies:
            new_company = create_object(Company, company)
            new_company.financial = all_financials[new_company.ticker]
            session.add(new_company)
        session.commit()
    # print("Database created successfully!")


if __name__ == "__main__":
    engine = create_engine("sqlite:///investor.db")
    if not exists('investor.db'):
        create_database(engine)
    print("Welcome to the Investor Program!")
    with Session(engine) as session:
        main_menu(session)
