# 파일 입출력 시 os 모듈을 사용하지 않으므로 주석 처리합니다.
# import os 

# --- 1. 데이터 모델링: Stock 클래스 정의 (전역) ---
class Stock:
    # 엑셀 헤더 순서: 종목명, 종목코드, 현재가, 전일대비, 등락률
    def __init__(self, name, code, price, change, rate):
        self.name = name        # 종목명 (A열)
        self.code = code        # 종목코드 (B열)
        self.price = price      # 현재가 (C열)
        self.change = change    # 전일대비 (D열)
        self.rate = rate        # 등락률 (E열)

    def evaluate(self):
        print(f"종목명: {self.name}, 현재가: {self.price}원, 전일대비: {self.change}, 등락률: {int(float(self.rate))}") 
              # [{self.code}]

# --- 2. 테스트용 CSV 파일 생성 함수 (전역) ---
def create_test_csv(filename="stock.csv"):
    # os.path.exists 대신 try/except FileNotFoundError 사용 (os 모듈 import 방지)
    try: 
        # 파일을 읽어봐서 존재하면(에러가 안 나면) 함수 종료
        with open(filename, "r", encoding="cp949") as f:
            return
        
    except FileNotFoundError:
        # 파일이 없으면 (에러가 나면) 새로 생성
        csv_data = [
            "종목명,종목코드,현재가,전일대비,등락률",  # 헤더
            "삼성전자,5930,75000,1000,1.35",      # 이미지 2행
            "SK하이닉스,660,130000,-2000,-1.52",    # 이미지 3행
            "LG에너지솔루션,373220,450000,5000,1.12",# 이미지 4행
            "현대차,5380,200000,0,0",          # 이미지 5행
            "NAVER,35420,220000,-3000,-1.34"      # 이미지 6행
        ]
        
        # 파일 생성 및 데이터 기록
        with open(filename, "rt", encoding="utf-8") as f:
            for line in csv_data:
                f.write(line + "\n")
        print(f"테스트용 파일 '{filename}'이 엑셀 이미지 데이터를 기반으로 생성되었습니다.")


# --- 3. 핵심 파싱 로직: CSV 파일을 읽어와 Stock 객체로 변환 (전역) ---
def getStocks():
    stocks = [] 
    
    with open("stock.csv", "rt", encoding="cp949") as f:
        
        for i, stock in enumerate(f.readlines()):
            
            if i == 0:
                continue 

            r1 = stock.strip()
            r2 = r1.split(",")
            
            # [NameError 해결] Stock 클래스가 전역에 정의되어 있으므로 사용 가능
            s = Stock(
                name=r2[0],       
                code=r2[1],       
                price=r2[2],      
                change=r2[3],     
                rate=r2[4]       
            )
            
            s.evaluate()
            stocks.append(s)

    # print(f"\n[파싱 완료] 총 {len(stocks)}개의 주식 종목이 객체로 생성되어 출력되었습니다.")
    return stocks

# --- 4. 메인 실행 함수 (전역 함수 호출 역할) ---
def main():
    # [NameError 해결] create_test_csv와 getStocks 함수가 전역에 있어 호출 가능
    create_test_csv()
    stock_objects = getStocks()


# --- 5. 프로그램 실행 시작점 ---
if __name__ == "__main__":
    main()