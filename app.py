from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from flask_migrate import Migrate
from sqlalchemy.sql import func
from flask_moment import Moment
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test_management.db'
app.config['SECRET_KEY'] = 'asdf1234!@#$asdf1234!@#$'  # 실제 사용 시 랜덤값으로 변경
db = SQLAlchemy(app)
migrate = Migrate(app, db)
moment = Moment(app)
# 로그인 관리 설정
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# DB 모델 정의
class User(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), unique=True)
	password = db.Column(db.String(100))
	suites = db.relationship('TestSuite', backref='user', lazy=True)


class TestCase(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	case_id = db.Column(db.String(50), unique=True, nullable=False)  # CASE-ID
	title = db.Column(db.String(100), nullable=False)
	precondition = db.Column(db.Text)  # Precondition(전제조건)
	steps = db.Column(db.Text)
	expected_result = db.Column(db.Text)
	suite_id = db.Column(db.Integer, db.ForeignKey('test_suite.id'), nullable=False)
	# 🔽 중복된 관계(backref 'test_cases') 제거
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	user = db.relationship('User', backref=db.backref('test_cases', lazy=True))
	created_at = db.Column(db.DateTime, default=func.now())
	status = db.Column(db.String(10), nullable=True)  # 상태값 (PASS, FAIL, NOT_RUN)

class TestSuite(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
	abbreviation = db.Column(db.String(10), nullable=False)  # 약칭 필드
	created_at = db.Column(db.DateTime, default=func.now())
	# 기존 test_cases 유지
	test_cases = db.relationship('TestCase', backref='suite', lazy=True)


class TestExecution(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	result = db.Column(db.String(20), nullable=False)
	executed_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
	test_case_id = db.Column(db.Integer, db.ForeignKey('test_case.id'), nullable=False)


# 로그인 관리
@login_manager.user_loader
def load_user(user_id):
	return User.query.get(int(user_id))


# 라우트 및 기능 확장
@app.route('/')
@login_required
def index():
	return redirect(url_for('dashboard'))


# 기존 dashboard 라우트 수정
@app.route('/dashboard')
@login_required
def dashboard():
	# 최신순으로 가져오는 쿼리 추가
	suites = TestSuite.query.filter_by(user_id=current_user.id).order_by(TestSuite.created_at.desc()).limit(10).all()
	cases = TestCase.query.join(TestSuite).filter(TestSuite.user_id == current_user.id).order_by(
		TestCase.created_at.desc()).limit(10).all()

	# 통계 데이터
	total_cases = len(cases)
	executions = TestExecution.query.join(TestCase).join(TestSuite).filter(TestSuite.user_id == current_user.id).all()

	pass_count = sum(1 for e in executions if e.result == 'PASS')
	fail_count = sum(1 for e in executions if e.result == 'FAIL')
	notrun_count = sum(1 for e in executions if e.result == 'NOT_RUN')

	return render_template('dashboard.html',
	                       suites=suites,
	                       cases=cases,
	                       total_cases=total_cases,
	                       pass_count=pass_count,
	                       fail_count=fail_count,
	                       notrun_count=notrun_count)


def dashboard_view(request):
	suites = Suite.objects.order_by('-created_at')[:10]  # 최근 생성된 상위 10개
	cases = TestCase.objects.order_by('-created_at')[:10]  # 최근 생성된 상위 10개
	return render(request, 'dashboard.html', {
		'suites':suites,
		'cases':cases,
	})

# [기존 라우트들에 @login_required 추가 및 user_id 필터링]
# [... 기존 코드 유지 (모든 데이터 조회 시 current_user.id 필터 적용 필요) ...]

# 로그인/회원가입 기능
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		user = User.query.filter_by(username=username).first()
		if user and check_password_hash(user.password, password):
			login_user(user)
			return redirect(url_for('dashboard'))
		flash('Invalid credentials')
	return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
	if request.method == 'POST':
		# 수정된 부분: method='pbkdf2:sha256' 사용
		hashed_pw = generate_password_hash(
			request.form['password'],
			method='pbkdf2:sha256'  # ← 여기가 핵심!
		)
		new_user = User(username=request.form['username'], password=hashed_pw)
		db.session.add(new_user)
		db.session.commit()
		flash('Registration successful!')
		return redirect(url_for('login'))
	return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login'))


# 데이터 저장 위치 안내 페이지
@app.route('/storage_info')
@login_required
def storage_info():
	return render_template('storage_info.html')



@app.route('/suites', methods=['GET'])
def suite_list():
	suites = TestSuite.query.all()  # 모든 Suite 가져오기
	return render_template('suite_list.html', suites=suites)


@app.route('/create_suite', methods=['POST'])
def create_suite():
	if not current_user.is_authenticated:
		return redirect('/login')  # 인증되지 않은 경우 로그인 페이지로 이동

	# Form 데이터 가져오기
	name = request.form['name']
	abbreviation = request.form['abbreviation']

	# 새로운 Suite 생성 (user_id 포함)
	new_suite = TestSuite(
		name=name,
		abbreviation=abbreviation,
		user_id=current_user.id  # 로그인된 사용자의 ID를 추가
	)

	# DB에 추가
	db.session.add(new_suite)
	db.session.commit()

	return redirect('/suites')  # Suite 생성 후 Suite 목록 화면으로 이동



@app.route('/suite/<int:suite_id>')
@login_required
def view_suite(suite_id):
	# 현재 사용자의 스위트만 조회하도록 수정 🔒
	suite = TestSuite.query.filter_by(
		id=suite_id,
		user_id=current_user.id
	).first_or_404()  # 404 에러 자동 처리
	return render_template('suite.html', suite=suite)


# 기존 코드 수정
@app.route('/case/<int:case_id>', methods=['GET'])
@login_required
def view_case(case_id):
	case = TestCase.query.join(TestSuite).filter(
		TestCase.id == case_id,
		TestSuite.user_id == current_user.id  # 🔑 TestSuite를 통해 사용자 필터링
	).first_or_404()
	return render_template('case.html', case=case)


def generate_case_id(suite):
	# 현재 Suite에 속한 Test Case의 갯수 확인
	existing_cases = TestCase.query.filter_by(suite_id=suite.id).count()

	# CASE-ID: 약칭 + (기존 Test Case 수 + 1)
	return f"{suite.abbreviation}{existing_cases + 1}"


@app.route('/add_case/<int:suite_id>', methods=['POST'])
@login_required
def add_case(suite_id):
	# 현재 사용자가 소유한 Suite인지 확인
	suite = TestSuite.query.filter_by(id=suite_id, user_id=current_user.id).first_or_404()

	# POST로 전달받은 데이터
	title = request.form.get('title', '').strip()
	precondition = request.form.get('precondition', '').strip()
	steps = request.form.get('steps', '').strip()
	expected_result = request.form.get('expected_result', '').strip()

	if not title:
		flash('Title is required.', 'danger')
		return redirect(url_for('view_suite', suite_id=suite_id))

	# CASE-ID 자동 생성
	try:
		case_id = generate_case_id(suite)
		print(f"Generated Case ID: {case_id}")
	except Exception as e:
		flash(f"Failed to generate Case ID: {e}", 'danger')
		return redirect(url_for('view_suite', suite_id=suite_id))

	# 새로운 Test Case 생성
	new_case = TestCase(
		case_id=case_id,
		title=title,
		precondition=precondition,
		steps=steps,
		expected_result=expected_result,
		suite_id=suite.id,
		user_id=current_user.id  # 현재 사용자의 ID 추가
	)

	# 데이터베이스에 저장
	try:
		db.session.add(new_case)
		db.session.commit()
		flash('Test Case added successfully!', 'success')
	except Exception as e:
		db.session.rollback()
		print(f"Database Error: {e}")
		flash(f"An error occurred while saving the case: {str(e)}", 'danger')

	# 스위트 페이지로 리다이렉트
	return redirect(url_for('view_suite', suite_id=suite_id))


@app.route('/update_case_result/<int:case_id>', methods=['POST'])
@login_required
def update_case_result(case_id):  # 기존 update_case에서 이름 변경
	result = request.form.get('result')

	if result not in ["PASS", "FAIL", "NOT_RUN"]:
		flash("Invalid result selected.", "danger")
		return redirect(request.referrer)

	case = TestCase.query.join(TestSuite).filter(
		TestCase.id == case_id,
		TestSuite.user_id == current_user.id
	).first_or_404()

	# 새로운 실행 결과 추가
	new_execution = TestExecution(
		result=result,
		test_case_id=case.id
	)
	db.session.add(new_execution)
	db.session.commit()

	flash(f"Test case '{case.title}' updated successfully.", "success")
	return redirect(request.referrer)

@app.route('/execute_case/<int:case_id>', methods=['POST'])
@login_required  # 로그인 필수
def execute_case(case_id):
	# 테스트 케이스가 현재 사용자와 연결된 케이스인지 확인
	case = TestCase.query.join(TestSuite).filter(
		TestCase.id == case_id,  # 케이스 ID 매칭
		TestSuite.user_id == current_user.id  # 현재 사용자 권한 확인
	).first_or_404()  # 없으면 404 에러 처리

	# 결과 폼 데이터 가져오기
	result = request.form.get('result')
	if result not in ["PASS", "FAIL", "NOT_RUN"]:
		flash("Invalid result selected. Please choose a valid result.", "danger")
		return redirect(url_for('view_case', case_id=case_id))  # 유효하지 않으면 다시

	# 실행 결과 저장
	case.status = result
	print(f"Updating status for case {case.id} to {result}")
	db.session.commit()

	# 성공 메시지 추가
	flash(f"Test case '{case.title}' executed and recorded as '{result}'.", "success")

	# 완료 후 원래 페이지로 리다이렉트
	return redirect(url_for('view_case', case_id=case_id))


@app.route('/update_case_details/<int:case_id>', methods=['POST'])
@login_required
def update_case_details(case_id):  # 또 다른 update_case 함수의 이름 변경
	# 현재 사용자가 소유한 Test Case인지 확인
	case = TestCase.query.join(TestSuite).filter(
		TestCase.id == case_id,
		TestSuite.user_id == current_user.id  # 현재 사용자 검사
	).first_or_404()

	# 수정 데이터 가져오기
	title = request.form.get('title', '').strip()
	precondition = request.form.get('precondition', '').strip()
	steps = request.form.get('steps', '').strip()
	expected_result = request.form.get('expected_result', '').strip()

	# 필수 필드 확인
	if not title or not steps or not expected_result:
		flash('Title, steps, and expected result are required.', 'danger')
		return redirect(url_for('view_case', case_id=case.id))

	# 변경사항 적용
	case.title = title
	case.precondition = precondition
	case.steps = steps
	case.expected_result = expected_result

	# 데이터베이스 저장
	try:
		db.session.commit()
		flash('Test Case updated successfully!', 'success')
	except Exception as e:
		db.session.rollback()
		flash(f'An error occurred: {str(e)}', 'danger')

	# 수정 후 다시 Test Case 페이지로 리다이렉트
	return redirect(url_for('view_case', case_id=case.id))


if __name__ == '__main__':
	with app.app_context():
		db.create_all()
	app.run(debug=True)
