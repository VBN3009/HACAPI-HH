import requests
from bs4 import BeautifulSoup
import re
import logging
from utils.helpers import safe_get, safe_post, check_link, safe_find_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HACSession:
    
    def __init__(self, username, password, base_url):
        if not check_link(base_url):
            raise ValueError(f"❌ Invalid HAC base URL: {base_url}")
        
        self.session = requests.Session()
        self.username = username
        self.password = password
        self.base_url = base_url.rstrip('/') + '/'
        self.logged_in = False
        self.auth_token = None
        self.last_auth_time = None

    def login(self):
        auth_url = f"{self.base_url}HomeAccess/Account/LogOn"
        
        try:
            # Step 1: Load login page
            response = safe_get(self.session, auth_url)
            if not response:
                logger.error("Failed to load login page.")
                return False

            logger.info(f"Visiting login page: {auth_url} (Status {response.status_code})")
            soup = BeautifulSoup(response.content, 'lxml')
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})

            if not token_input:
                logger.error("Login token not found.")
                return False

            # Step 2: Prepare and submit login form
            payload = {
                '__RequestVerificationToken': token_input['value'],
                'SCKTY00328510CustomEnabled': True,
                'SCKTY00436568CustomEnabled': True,
                'Database': 10,
                'VerificationOption': 'UsernamePassword',
                'LogOnDetails.UserName': self.username,
                'tempUN': '',
                'tempPW': '',
                'LogOnDetails.Password': self.password
            }

            login_response = safe_post(self.session, auth_url, data=payload)
            
            if not login_response or login_response.status_code != 200:
                logger.error("Login POST failed or returned non-200 status.")
                return False

            # Store authentication token from response
            self.auth_token = login_response.cookies.get('AuthToken')
            
            # Verify login success
            if "LogOn" in login_response.url or "login" in login_response.text.lower():
                logger.warning("Login attempt remained on login page — bad credentials.")
                return False

            # Login succeeded
            logger.info("Login successful.")
            self.logged_in = True
            return True

        except Exception as e:
            logger.error(f"Login failed with error: {str(e)}")
            return False

    def get_info(self):
        if not self.logged_in:
            self.login()

        url = self.base_url + 'HomeAccess/Content/Student/Registration.aspx'
        logger.info(f"Fetching registration info from {url}")
        
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Failed to fetch registration page.")
            return None

        soup = BeautifulSoup(response.text, 'lxml')

        return {
            'name': safe_find_text(soup, 'plnMain_lblRegStudentName'),
            'grade': safe_find_text(soup, 'plnMain_lblGrade'),
            'school': safe_find_text(soup, 'plnMain_lblBuildingName'),
            'dob': safe_find_text(soup, 'plnMain_lblBirthDate'),
            'counselor': safe_find_text(soup, 'plnMain_lblCounselor'),
            'language': safe_find_text(soup, 'plnMain_lblLanguage'),
            'cohort_year': safe_find_text(soup, 'plnMain_lblCohortYear')
        }

    
    def get_transcript(self):
        logger.info("Fetching transcript...")
        if not self.logged_in:
            self.login()

        url = self.base_url + "HomeAccess/Content/Student/Transcript.aspx"
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Could not fetch transcript page.")
            return None

        soup = BeautifulSoup(response.text, 'lxml')
        transcript = {}

        # Parse semester-by-semester transcript
        for section in soup.find_all('td', class_='sg-transcript-group'):
            semester_data = {}
            table1 = section.find_next('table')
            table2 = table1.find_next('table')
            table3 = table2.find_next('table')

            for span in table1.find_all('span'):
                if "YearValue" in span.get('id', ''):
                    semester_data['year'] = span.text.strip()
                if "GroupValue" in span.get('id', ''):
                    semester_data['semester'] = span.text.strip()
                if "GradeValue" in span.get('id', ''):
                    semester_data['grade'] = span.text.strip()
                if "BuildingValue" in span.get('id', ''):
                    semester_data['school'] = span.text.strip()

            semester_data['data'] = [
                [td.text.strip() for td in tr.find_all('td')]
                for tr in table2.find_all('tr') if tr.find_all('td')
            ]

            for label in table3.find_all('label'):
                if "CreditValue" in label.get('id', ''):
                    semester_data['credits'] = label.text.strip()

            label = f"{semester_data['year']} - Semester {semester_data['semester']}"
            transcript[label] = semester_data

        # Parse cumulative GPA info
        gpa_table = soup.find('table', id='plnMain_rpTranscriptGroup_tblCumGPAInfo')
        if not gpa_table:
            logger.warning("Cumulative GPA table not found.")
            return None

        for row in gpa_table.find_all('tr', class_='sg-asp-table-data-row'):
            for label in row.find_all('span'):
                if "GPADescr" in label.get('id', ''):
                    value = label.find_next('span')
                    transcript[label.text.strip()] = value.text.strip()

        rank_field = soup.find('span', id='plnMain_rpTranscriptGroup_lblGPARank3')
        transcript['Rank'] = rank_field.text.strip() if rank_field else "Unknown"

        logger.info("Transcript successfully parsed.")
        return transcript
    
    def get_name(self):
        if not self.logged_in:
            self.login()

        url = self.base_url + 'HomeAccess/Home/WeekView'
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Failed to fetch WeekView page.")
            return None

        soup = BeautifulSoup(response.text, 'lxml')

        # 🔍 Look for any <span> with title "Change Student"
        name_span = soup.find('span', attrs={"title": "Change Student"})
        if name_span:
            student_name = name_span.text.strip()
            logger.info(f"✅ Student name extracted: {student_name}")
            return student_name

        logger.warning("❌ Student name span with title 'Change Student' not found.")
        return None

    def fetch_class_assignments(self, filter_class=None):
        if not self.logged_in:
            self.login()

        assignments_url = f"{self.base_url}HomeAccess/Content/Student/Assignments.aspx"
        response = safe_get(self.session, assignments_url)
        if not response:
            logger.warning("Could not fetch assignments page.")
            return None

        logger.info(f"Fetching assignment data from: {assignments_url} (Status {response.status_code})")
        soup = BeautifulSoup(response.text, 'lxml')
        course_data = {}

        for section in soup.find_all('div', class_='AssignmentClass'):
            header = section.find('div', class_='sg-header')
            if not header:
                continue

            heading_link = header.find('a', class_='sg-header-heading')
            heading_span = header.find('span', class_='sg-header-heading')

            course_title = heading_link.text.strip().split("-", 1)[-1].strip() if heading_link else "Unknown Course"
            course_code = heading_link.text.strip().split("-", 1)[0].strip() if heading_link else "0000"
            average_text = heading_span.text.strip().split(":")[-1].strip() if heading_span else ""

            assignments, categories = [], []

            for tbl in section.find_all('table', class_='sg-asp-table'):
                rows = [
                    [td.text.strip().replace("*", "") for td in tr.find_all('td')]
                    for tr in tbl.find_all('tr') if tr.find_all('td')
                ]
                tbl_id = tbl.get('id', '')
                if 'CourseAssignments' in tbl_id:
                    assignments = rows
                elif 'CourseCategories' in tbl_id:
                    categories = rows

            course_data[course_title] = {
                'code': course_code,
                'average': average_text,
                'assignments': assignments,
                'categories': categories
            }

        if not course_data:
            logger.warning("No assignment data found for any class.")
            return None

        if filter_class:
            filter_class = filter_class.lower()
            filtered_data = {
                name: data for name, data in course_data.items()
                if filter_class in name.lower() or filter_class in data.get("code", "").lower()
            }
            if not filtered_data:
                logger.warning(f"No matching class found for filter: {filter_class}")
                return None
            logger.info(f"Filtered assignment data for class: {filter_class}")
            return filtered_data

        logger.info("Fetched assignment data for all classes.")
        return course_data


    def get_report(self, mp_filter=None):
        logger.info(f"Fetching progress report{' for MP: ' + mp_filter if mp_filter else ''}...")

        if not self.logged_in:
            self.login()

        progress_url = self.base_url + 'HomeAccess/Content/Student/InterimProgress.aspx'
        response = safe_get(self.session, progress_url)
        if not response:
            logger.warning("Could not fetch progress report page.")
            return None

        logger.info(f"Fetched progress data from: {progress_url} (Status {response.status_code})")
        soup = BeautifulSoup(response.text, 'lxml')

        rows = [
            [td.text.strip() for td in tr.find_all('td')]
            for tr in soup.find_all('tr', class_='sg-asp-table-data-row')
            if tr.find_all('td')
        ]

        if not rows:
            logger.warning("No progress report rows found.")
            return None

        if mp_filter:
            logger.info(f"Filtering for MP: {mp_filter}")
            mp_filter = mp_filter.lower()
            rows = [row for row in rows if any(mp_filter in cell.lower() for cell in row)]

            if not rows:
                logger.warning("No matching rows after filter.")
                return None

        headers = ["Class Code", "Class", "Period", "Teacher", "Room", "Average"]
        trimmed_data = [row[:6] + [""] * (6 - len(row)) for row in rows]

        logger.info("Progress report parsed successfully.")
        return {
            "headers": headers,
            "data": trimmed_data
        }

    def get_classes(self):
        if not self.logged_in:
            self.login()

        url = self.base_url + 'HomeAccess/Content/Student/Assignments.aspx'
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Could not fetch class list.")
            return None

        logger.info(f"Fetching class list from {url}")
        soup = BeautifulSoup(response.text, 'lxml')

        classes = []
        for div in soup.find_all('div', class_='AssignmentClass'):
            header = div.find('div', class_='sg-header')
            if not header:
                continue
            name = header.find('a', class_='sg-header-heading')
            if name:
                class_name = re.sub(r'^\d+\s*-*\s*', '', name.text.strip())
                classes.append(class_name)

        if not classes:
            logger.warning("No classes found in the assignments page.")
            return None

        logger.info(f"Found {len(classes)} classes.")
        return {'classes': classes}

    def get_averages(self):
        if not self.logged_in:
            self.login()

        url = self.base_url + 'HomeAccess/Content/Student/Assignments.aspx'
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Could not fetch class averages.")
            return None

        logger.info(f"Fetching class averages from {url}")
        soup = BeautifulSoup(response.text, 'lxml')

        result = {}
        for div in soup.find_all('div', class_='AssignmentClass'):
            header = div.find('div', class_="sg-header")
            if not header:
                continue
            name_tag = header.find('a', class_='sg-header-heading')
            avg_tag = header.find('span', class_='sg-header-heading')

            if not name_tag or not avg_tag:
                continue

            name = name_tag.text.strip()
            avg_text = avg_tag.text.strip()
            class_name = re.sub(r'^\d+\s*-*\s*', '', name)
            average = avg_text.split(":")[-1].strip()
            result[class_name] = average

        if not result:
            logger.warning("No averages found in the assignments page.")
            return None

        logger.info(f"Found averages for {len(result)} classes.")
        return result

    def get_rank(self):
        if not self.logged_in:
            self.login()

        url = self.base_url + "HomeAccess/Content/Student/Transcript.aspx"
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Could not fetch transcript page for rank.")
            return None

        logger.info(f"Fetching rank from {url}")
        soup = BeautifulSoup(response.text, 'lxml')

        rank = soup.find('span', id='plnMain_rpTranscriptGroup_lblGPARank3')
        if rank:
            logger.info(f"Student Rank found: {rank.text.strip()}")
            return rank.text.strip()
        else:
            logger.warning("Rank field not found in transcript page.")
            return None
        
    def get_students(self):
        if not self.logged_in:
            self.login()

        url = self.base_url + "HomeAccess/Frame/StudentPicker"
        response = safe_get(self.session, url)
        if not response:
            logger.warning("Failed to fetch StudentPicker.")
            return None

        soup = BeautifulSoup(response.text, "lxml")
        form = soup.find("form", id="StudentPicker")
        if not form:
            logger.warning("StudentPicker form not found.")
            return None

        students = []
        for label in form.find_all("label", class_="sg-student-picker-row"):
            input_tag = label.find("input", {"name": "studentId"})
            if not input_tag:
                continue
            student_id = input_tag.get("value")
            name_span = label.find("span", class_="sg-picker-student-name")
            name = name_span.text.strip() if name_span else "Unknown"
            students.append({"id": student_id, "name": name})

        return students
    
    def switch_student(self, student_id):
        try:
            if not self.logged_in:
                logger.info("🔒 Not logged in — attempting login")
                if not self.login():
                    return False

            # First try the modern API endpoint
            switch_url = f"{self.base_url}HomeAccess/Frame/SwitchStudent"
            payload = {"studentId": student_id}
            headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            switch_response = safe_post(self.session, switch_url, data=payload, headers=headers, allow_redirects=True)
            
            if switch_response and switch_response.status_code in [200, 302]:
                logger.info("✅ Switch request successful, verifying...")
                
                # Force a new page load to refresh session context
                refresh_response = safe_get(self.session, f"{self.base_url}HomeAccess/Home")
                if not refresh_response or refresh_response.status_code != 200:
                    logger.warning("Failed to refresh session context")
                    return False

                # Get current student info
                current = self.get_active_student()
                if not current:
                    logger.warning("Failed to get active student after switch")
                    return False

                # Get student list to verify
                students = self.get_students()
                if not students:
                    logger.warning("Failed to get student list for verification")
                    return False

                # Find target student name
                target_student = next((s for s in students if s["id"] == student_id), None)
                if not target_student:
                    logger.warning(f"Target student ID {student_id} not found in student list")
                    return False

                # Verify switch was successful
                if current.get("name") == target_student["name"]:
                    logger.info(f"✅ Switch verified - now active: {current['name']}")
                    return True
                else:
                    logger.warning(f"❌ Switch failed - still active: {current['name']}")
                    return False

            # If modern API fails, try legacy endpoint
            legacy_url = f"{self.base_url}HomeAccess/Frame/SwitchStudent/{student_id}"
            legacy_response = safe_get(self.session, legacy_url, allow_redirects=True)
            
            if legacy_response and legacy_response.status_code in [200, 302]:
                logger.info("✅ Legacy switch successful, verifying...")
                return self.verify_student_switch(student_id)

            logger.warning("❌ All switch attempts failed")
            return False

        except Exception as e:
            logger.error(f"Error during student switch: {str(e)}")
            return False

    def verify_student_switch(self, student_id):
        """Verify the student switch was successful"""
        try:
            # Force refresh session context
            refresh_response = safe_get(self.session, f"{self.base_url}HomeAccess/Home")
            if not refresh_response or refresh_response.status_code != 200:
                return False
            
            # Get current active student
            current = self.get_active_student()
            if not current:
                return False
                
            # Get all students for verification
            students = self.get_students()
            if not students:
                return False
                
            # Find target student
            target_student = next((s for s in students if s["id"] == student_id), None)
            if not target_student:
                return False
                
            # Verify switch
            if current.get("name") == target_student["name"]:
                logger.info(f"✅ Switch verified - now active: {current['name']}")
                return True
                
            logger.warning(f"❌ Switch failed - still active: {current['name']}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying switch: {str(e)}")
            return False

    def get_active_student(self):
        """
        Returns the currently selected student name (and ID, if you like)
        by scraping the banner chooser on the Home page.
        """
        if not self.logged_in:
            self.login()

        home_url = self.base_url + "HomeAccess/Home"
        logger.info(f"🌐 [SESSION] GET {home_url} to fetch active student")
        resp = self.session.get(home_url)
        logger.debug(f"🔁 [SESSION] Home page status: {resp.status_code}")
        if resp.status_code != 200:
            logger.warning(f"❌ [SESSION] could not fetch Home page: {resp.status_code}")
            return None

        soup = BeautifulSoup(resp.text, "lxml")
        chooser = soup.find("div", class_="sg-banner-chooser")
        if not chooser:
            logger.warning("❌ [SESSION] banner chooser not found")
            return None

        span = chooser.find(
            "span",
            class_="sg-banner-text sg-banner-text-color sg-add-change-student"
        )
        if not span:
            logger.warning("❌ [SESSION] active‑student span not found")
            return None

        name = span.text.strip()
        logger.info(f"✅ [SESSION] active student: {name}")
        return {"name": name}
