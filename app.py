from flask import Flask, render_template, request, redirect, url_for, session
from pypdf import PdfReader
import re

app = Flask(__name__)
app.secret_key = "smart-resume-analyzer-secret-key"

# ==========================================================
# SKILL DATABASE
# ==========================================================

SKILL_ALIASES = {

    # ---------------- PROGRAMMING ----------------
    "python": [
        "python",
        "python programming",
        "python language"
    ],

    "java": [
        "java",
        "java programming",
        "java language"
    ],

    "javascript": [
        "javascript",
        "java script",
        "js"
    ],

    "c++": [
        "c++",
        "cpp",
        "c plus plus"
    ],

    "c": [
        "c programming",
        "c language"
    ],

    # ---------------- WEB DEVELOPMENT ----------------
    "html": [
        "html",
        "html5"
    ],

    "css": [
        "css",
        "css3"
    ],

    "bootstrap": [
        "bootstrap"
    ],

    "tailwind css": [
        "tailwind css",
        "tailwindcss"
    ],

    "react": [
        "react",
        "reactjs",
        "react.js"
    ],

    "node.js": [
        "node.js",
        "nodejs",
        "node js"
    ],

    "express": [
        "express",
        "express.js",
        "expressjs"
    ],

    "web development": [
        "web development",
        "web developer",
        "web development skills"
    ],

    # ---------------- BACKEND ----------------
    "flask": [
        "flask",
        "flask framework"
    ],

    "django": [
        "django",
        "django framework"
    ],

    "rest api": [
        "rest api",
        "rest apis",
        "restful api",
        "restful apis"
    ],

    "api development": [
        "api development",
        "api development skills"
    ],

    # ---------------- DATABASE ----------------
    "sql": [
        "sql",
        "structured query language"
    ],

    "mysql": [
        "mysql",
        "my sql"
    ],

    "mongodb": [
        "mongodb",
        "mongo db"
    ],

    "postgresql": [
        "postgresql",
        "postgres"
    ],

    # ---------------- TOOLS ----------------
    "git": [
        "git",
        "git version control"
    ],

    "github": [
        "github",
        "git hub"
    ],

    "gitlab": [
        "gitlab",
        "git lab"
    ],

    "docker": [
        "docker",
        "docker containers",
        "containerization"
    ],

    # ---------------- CLOUD / OS ----------------
    "aws": [
        "aws",
        "amazon web services"
    ],

    "azure": [
        "azure",
        "microsoft azure"
    ],

    "linux": [
        "linux",
        "linux operating system"
    ],

    # ---------------- DATA / AI ----------------
    "pandas": [
        "pandas",
        "python pandas"
    ],

    "numpy": [
        "numpy",
        "python numpy"
    ],

    "machine learning": [
        "machine learning",
        "machine-learning",
        "ml"
    ],

    "deep learning": [
        "deep learning",
        "deep-learning"
    ],

    "data science": [
        "data science",
        "data scientist"
    ],

    # ---------------- COMPUTER SCIENCE ----------------
    "data structures": [
        "data structures",
        "data structure",
        "data structures and algorithms"
    ],

    "algorithms": [
        "algorithms",
        "algorithm"
    ],

    "object oriented programming": [
        "object oriented programming",
        "object-oriented programming",
        "oop"
    ],

    "operating systems": [
        "operating systems",
        "operating system",
        "os"
    ],

    "computer networks": [
        "computer networks",
        "computer network",
        "networking"
    ],

    # ---------------- SOFT SKILLS ----------------
    "communication": [
        "communication",
        "communication skills"
    ],

    "problem solving": [
        "problem solving",
        "problem-solving",
        "problem solving skills"
    ],

    "teamwork": [
        "teamwork",
        "team work",
        "team player"
    ],

    "time management": [
        "time management",
        "time-management"
    ]
}


# ==========================================================
# TEXT NORMALIZATION
# ==========================================================

def normalize_text(text):
    """
    Makes text easier to search while preserving
    useful information such as dates and skill names.
    """

    if not text:
        return ""

    text = text.replace("\xa0", " ")
    text = text.replace("\r", "\n")

    # Convert multiple spaces into one
    text = re.sub(r"[ \t]+", " ", text)

    # Convert excessive blank lines into one
    text = re.sub(r"\n\s*\n+", "\n", text)

    return text.strip()


# ==========================================================
# SKILL DETECTION
# ==========================================================

def contains_skill(text, aliases):
    """
    Checks whether a skill alias actually appears
    as a separate word/phrase.
    """

    for alias in aliases:

        pattern = r"(?<!\w)" + re.escape(alias) + r"(?!\w)"

        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


def detect_skills(text):
    """
    Detect canonical skills from resume/JD text.
    """

    detected_skills = []

    for skill, aliases in SKILL_ALIASES.items():

        if contains_skill(text, aliases):
            detected_skills.append(skill)

    return detected_skills


# ==========================================================
# RESUME SECTION HELPERS
# ==========================================================

SECTION_HEADINGS = {
    "experience",
    "work experience",
    "professional experience",
    "work history",
    "employment history",
    "employment",
    "internship",
    "internships",
    "education",
    "skills",
    "technical skills",
    "projects",
    "personal projects",
    "academic projects",
    "certifications",
    "certificates",
    "achievements",
    "languages",
    "interests",
    "hobbies",
    "summary",
    "professional summary",
    "objective",
    "profile",
    "contact",
    "declaration"
}


def clean_heading(line):
    """
    Converts a possible heading into a comparable form.
    """

    cleaned = re.sub(r"[^a-zA-Z ]", "", line)
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned.strip().lower()


def is_section_heading(line):
    return clean_heading(line) in SECTION_HEADINGS


def clean_resume_line(line):
    """
    Removes common bullet symbols and unnecessary spaces.
    """

    line = re.sub(
        r"^[•●▪◦\-*]+\s*",
        "",
        line
    )

    return line.strip()


# ==========================================================
# DATE DETECTION
# ==========================================================

MONTH_PATTERN = (
    r"(Jan|January|Feb|February|Mar|March|Apr|April|May|"
    r"Jun|June|Jul|July|Aug|August|Sep|September|Oct|October|"
    r"Nov|November|Dec|December)"
)

DATE_PATTERN = re.compile(
    r"("
    r"(?:"
    + MONTH_PATTERN +
    r")\s+\d{4}"
    r"\s*[-–—to]+\s*"
    r"(?:"
    + MONTH_PATTERN +
    r")\s+\d{4}"
    r"|"
    r"(?:"
    + MONTH_PATTERN +
    r")\s+\d{4}"
    r"\s*[-–—to]+\s*"
    r"(?:Present|Current)"
    r"|"
    r"\d{4}"
    r"\s*[-–—to]+\s*"
    r"(?:\d{4}|Present|Current)"
    r")",
    re.IGNORECASE
)


def find_date(line):
    match = DATE_PATTERN.search(line)

    if match:
        return match.group(0).strip()

    return ""


# ==========================================================
# EXPERIENCE SECTION EXTRACTION
# ==========================================================

def get_experience_section(resume_text):

    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    start_index = None

    experience_headings = {
        "experience",
        "work experience",
        "professional experience",
        "work history",
        "employment history",
        "employment",
        "internship",
        "internships"
    }

    for index, line in enumerate(lines):

        heading = clean_heading(line)

        if heading in experience_headings:

            start_index = index + 1
            break

    if start_index is None:
        return []

    section_lines = []

    for line in lines[start_index:]:

        heading = clean_heading(line)

        if heading in SECTION_HEADINGS:
            break

        section_lines.append(clean_resume_line(line))

    return section_lines


# ==========================================================
# BUILD EXPERIENCE ENTRY
# ==========================================================

def build_experience_entry(lines):

    if not lines:
        return None

    lines = [
        clean_resume_line(line)
        for line in lines
        if line.strip()
    ]

    if not lines:
        return None

    # ------------------------------------------------------
    # Find date
    # ------------------------------------------------------

    duration = ""

    for line in lines:

        date = find_date(line)

        if date:
            duration = date
            break

    # ------------------------------------------------------
    # Remove date from content
    # ------------------------------------------------------

    content_lines = []

    for line in lines:

        if duration:

            line_without_date = re.sub(
                re.escape(duration),
                "",
                line,
                flags=re.IGNORECASE
            ).strip()

            if line_without_date:
                content_lines.append(line_without_date)

        else:
            content_lines.append(line)

    if not content_lines:
        return None

    # ------------------------------------------------------
    # Determine title and company
    # ------------------------------------------------------

    title = ""
    company = ""

    # Common pattern:
    #
    # Software Developer Intern
    # ABC Technologies
    #
    # or:
    #
    # ABC Technologies
    # Software Developer Intern

    if len(content_lines) >= 1:
        title = content_lines[0]

    if len(content_lines) >= 2:
        company = content_lines[1]

    # ------------------------------------------------------
    # Description
    # ------------------------------------------------------

    description_lines = []

    if len(content_lines) > 2:

        description_lines = content_lines[2:]

    description = " ".join(description_lines)

    # ------------------------------------------------------
    # Technologies used
    # ------------------------------------------------------

    technologies = detect_skills(
        " ".join(content_lines)
    )

    # ------------------------------------------------------
    # Return structured experience
    # ------------------------------------------------------

    return {
        "title": title,
        "company": company,
        "duration": duration,
        "duration_months": parse_date_range_months(duration),
        "description": description,
        "technologies": technologies
    }


# ==========================================================
# EXPERIENCE EXTRACTION
# ==========================================================

def get_experience_section_by_heading(resume_text, target_headings):

    lines = [
        line.strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    start_index = None

    for index, line in enumerate(lines):
        if clean_heading(line) in target_headings:
            start_index = index + 1
            break

    if start_index is None:
        return []

    section_lines = []

    for line in lines[start_index:]:
        if clean_heading(line) in SECTION_HEADINGS:
            break
        section_lines.append(clean_resume_line(line))

    return section_lines


def extract_experience_from_lines(section_lines):

    if not section_lines:
        return []

    experiences = []
    date_positions = []

    for index, line in enumerate(section_lines):
        if find_date(line):
            date_positions.append(index)

    if date_positions:
        for position, start_index in enumerate(date_positions):
            if position + 1 < len(date_positions):
                end_index = date_positions[position + 1]
            else:
                end_index = len(section_lines)

            entry_start = max(0, start_index - 2)
            entry_lines = section_lines[entry_start:end_index]
            entry = build_experience_entry(entry_lines)

            if entry:
                experiences.append(entry)
    else:
        entry = build_experience_entry(section_lines)
        if entry:
            experiences.append(entry)

    return experiences


def extract_experience(resume_text):

    experiences = []

    main_section_lines = get_experience_section(resume_text)

    if main_section_lines:
        experiences.extend(
            extract_experience_from_lines(main_section_lines)
        )

    # Also inspect a separate Internship section when one exists.
    internship_lines = get_experience_section_by_heading(
        resume_text,
        {"internship", "internships"}
    )

    if internship_lines:
        internship_experiences = extract_experience_from_lines(
            internship_lines
        )

        for internship in internship_experiences:
            duplicate = any(
                internship.get("title") == existing.get("title")
                and internship.get("company") == existing.get("company")
                and internship.get("duration") == existing.get("duration")
                for existing in experiences
            )

            if not duplicate:
                experiences.append(internship)

    return experiences


# ==========================================================
# EXPERIENCE ANALYSIS HELPERS
# ==========================================================

def months_to_text(months):
    months = max(0, int(months or 0))
    years = months // 12
    remaining_months = months % 12
    parts = []
    if years:
        parts.append(f"{years} year" + ("s" if years != 1 else ""))
    if remaining_months:
        parts.append(f"{remaining_months} month" + ("s" if remaining_months != 1 else ""))
    return " ".join(parts) if parts else "0 months"


def parse_explicit_duration(text):
    if not text:
        return 0
    year_match = re.search(r"(\d+(?:\.\d+)?)\s*years?", text, re.IGNORECASE)
    month_match = re.search(r"(\d+)\s*months?", text, re.IGNORECASE)
    total = 0
    if year_match:
        total += round(float(year_match.group(1)) * 12)
    if month_match:
        total += int(month_match.group(1))
    return total


def parse_date_range_months(date_text):
    if not date_text:
        return 0
    explicit = parse_explicit_duration(date_text)
    if explicit:
        return explicit
    month_numbers = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }
    normalized = re.sub(r"[–—]", "-", date_text.strip())
    normalized = re.sub(r"\s+", " ", normalized)
    month_word = r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
    match = re.search(rf"({month_word})\s+(\d{{4}})\s*(?:-|to)\s*({month_word})\s+(\d{{4}})", normalized, re.IGNORECASE)
    if match:
        start_month = month_numbers[match.group(1).lower()[:3]]
        start_year = int(match.group(2))
        end_month = month_numbers[match.group(3).lower()[:3]]
        end_year = int(match.group(4))
        return max(0, (end_year - start_year) * 12 + (end_month - start_month) + 1)
    match = re.search(rf"({month_word})\s+(\d{{4}})\s*(?:-|to)\s*(Present|Current)", normalized, re.IGNORECASE)
    if match:
        from datetime import datetime
        start_month = month_numbers[match.group(1).lower()[:3]]
        start_year = int(match.group(2))
        now = datetime.now()
        return max(0, (now.year - start_year) * 12 + (now.month - start_month) + 1)
    match = re.search(r"(\d{4})\s*(?:-|to)\s*(\d{4}|Present|Current)", normalized, re.IGNORECASE)
    if match:
        start_year = int(match.group(1))
        end_value = match.group(2)
        if end_value.lower() in {"present", "current"}:
            from datetime import datetime
            now = datetime.now()
            return max(0, (now.year - start_year) * 12 + now.month)
        return max(0, (int(end_value) - start_year) * 12 + 12)
    return 0


def parse_job_experience_requirement(job_description):

    text = job_description or ""
    lower = text.lower()

    no_experience_patterns = [
        r"no\s+(?:prior\s+|previous\s+)?experience\s+(?:is\s+)?required",
        r"experience\s+(?:is\s+)?not\s+required",
        r"no\s+experience\s+needed",
        r"fresh(?:er|ers|graduate|graduates)\s+(?:are\s+)?welcome",
        r"open\s+to\s+fresh(?:er|ers|graduates)"
    ]

    if any(re.search(pattern, lower) for pattern in no_experience_patterns):
        return {
            "type": "none",
            "min_months": 0,
            "max_months": 0,
            "text": "No experience required",
            "status_label": "No experience required"
        }

    # Supports common forms such as:
    # 1-2 years of experience
    # 0-2 years frontend development
    # 2 years professional experience
    range_pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*(?:-|–|—|to)\s*"
        r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?)\b",
        re.IGNORECASE
    )

    single_pattern = re.compile(
        r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?)\b",
        re.IGNORECASE
    )

    match = range_pattern.search(text)

    if match:
        context = lower[
            max(0, match.start() - 100):
            min(len(lower), match.end() + 100)
        ]

        experience_context = bool(re.search(
            r"experience|work|professional|employment|development|developer|"
            r"frontend|backend|full[- ]?stack|role|position|graduate|fresher|intern",
            context
        ))

        if experience_context:
            first = float(match.group(1))
            second = float(match.group(2))
            unit = match.group(3).lower()
            multiplier = 12 if unit.startswith(("year", "yr")) else 1
            minimum = round(first * multiplier)
            maximum = round(second * multiplier)

            preferred = bool(re.search(
                r"preferred|desirable|nice\s+to\s+have|plus|bonus",
                context
            ))

            if multiplier == 12:
                unit_text = "year" if first == 1 and second == 1 else "years"
            else:
                unit_text = "month" if first == 1 and second == 1 else "months"

            range_text = (
                f"{int(first) if first.is_integer() else first:g}–"
                f"{int(second) if second.is_integer() else second:g} "
                f"{unit_text}"
            )

            return {
                "type": "preferred" if preferred else "required",
                "min_months": minimum,
                "max_months": maximum,
                "text": range_text,
                "status_label": "Preferred experience" if preferred else "Required experience"
            }

    # Supports: Experience: 6 months preferred
    label_first_pattern = re.compile(
        r"experience\s*(?:required|preferred|desired|needed)?\s*[:\-]?\s*"
        r"(\d+(?:\.\d+)?)\s*(years?|yrs?|months?)\b",
        re.IGNORECASE
    )

    label_match = label_first_pattern.search(text)

    if label_match:
        value = float(label_match.group(1))
        unit = label_match.group(2).lower()
        multiplier = 12 if unit.startswith(("year", "yr")) else 1
        minimum = round(value * multiplier)
        context = lower[
            max(0, label_match.start() - 80):
            min(len(lower), label_match.end() + 80)
        ]
        preferred = bool(re.search(
            r"preferred|desirable|nice\s+to\s+have|plus|bonus",
            context
        ))

        return {
            "type": "preferred" if preferred else "required",
            "min_months": minimum,
            "max_months": minimum,
            "text": months_to_text(minimum),
            "status_label": "Preferred experience" if preferred else "Required experience"
        }

    match = single_pattern.search(text)

    if match:
        context = lower[
            max(0, match.start() - 100):
            min(len(lower), match.end() + 100)
        ]

        experience_context = bool(re.search(
            r"experience|work|professional|employment|development|developer|"
            r"frontend|backend|full[- ]?stack|role|position|graduate|fresher|intern",
            context
        ))

        if experience_context:
            value = float(match.group(1))
            unit = match.group(2).lower()
            multiplier = 12 if unit.startswith(("year", "yr")) else 1
            minimum = round(value * multiplier)

            preferred = bool(re.search(
                r"preferred|desirable|nice\s+to\s+have|plus|bonus",
                context
            ))

            return {
                "type": "preferred" if preferred else "required",
                "min_months": minimum,
                "max_months": minimum,
                "text": months_to_text(minimum),
                "status_label": "Preferred experience" if preferred else "Required experience"
            }

    return {
        "type": "not_specified",
        "min_months": 0,
        "max_months": 0,
        "text": "Not specified",
        "status_label": "Experience not specified"
    }


def calculate_candidate_experience(experiences):
    professional_months = 0
    internship_months = 0
    for experience in experiences:
        title = (experience.get("title") or "").lower()
        company = (experience.get("company") or "").lower()
        months = int(experience.get("duration_months") or 0)
        if "intern" in f"{title} {company}":
            internship_months += months
        else:
            professional_months += months
    return professional_months, internship_months


def analyze_experience_requirement(job_description, experiences):
    requirement = parse_job_experience_requirement(job_description)
    professional_months, internship_months = calculate_candidate_experience(experiences)
    result = {
        **requirement,
        "candidate_months": professional_months,
        "candidate_display": months_to_text(professional_months),
        "internship_months": internship_months,
        "internship_display": months_to_text(internship_months),
        "gap_months": 0,
        "status": "",
        "status_title": "",
        "status_message": "",
        "status_class": "experience-neutral"
    }
    if requirement["type"] == "none":
        result.update({"status": "not_required", "status_title": "Experience not required", "status_message": "The job description does not require prior professional experience.", "status_class": "experience-neutral"})
    elif requirement["type"] == "not_specified":
        result.update({"status": "not_specified", "status_title": "Experience requirement not specified", "status_message": "The job description does not state a clear experience requirement.", "status_class": "experience-neutral"})
    elif requirement["type"] == "required":
        if professional_months >= requirement["min_months"]:
            result.update({"status": "met", "status_title": "Experience requirement met", "status_message": "Your professional experience meets the minimum experience requirement stated in the job description.", "status_class": "experience-success"})
        else:
            gap = max(0, requirement["min_months"] - professional_months)
            result.update({"status": "not_met", "gap_months": gap, "status_title": "Experience requirement not met", "status_message": "Your professional experience is below the minimum experience requirement stated in the job description.", "status_class": "experience-danger"})
    else:
        if professional_months >= requirement["min_months"]:
            result.update({"status": "preferred_met", "status_title": "Preferred experience met", "status_message": "Your professional experience meets the preferred experience level mentioned in the job description.", "status_class": "experience-success"})
        else:
            result.update({"status": "preferred_gap", "status_title": "Preferred experience not reached", "status_message": "The job description lists this experience as preferred; your resume shows less professional experience.", "status_class": "experience-warning"})
    return result


app.jinja_env.globals["months_to_text"] = months_to_text


# ==========================================================
# RECOMMENDATION
# ==========================================================


def get_match_information(score):

    if score >= 80:

        return (
            "Strong Match",
            "Your resume matches most of the skills required "
            "for this job. You have strong skill alignment."
        )

    elif score >= 60:

        return (
            "Good Match",
            "Your resume matches many of the required skills. "
            "Adding the missing skills could improve your match."
        )

    elif score >= 40:

        return (
            "Average Match",
            "Your resume has some relevant skills, but several "
            "job requirements are missing. Consider improving "
            "the missing skills."
        )

    else:

        return (
            "Low Match",
            "There is a limited skill match between your resume "
            "and this job description. Consider developing the "
            "missing skills."
        )


# ==========================================================
# HOME PAGE
# ==========================================================

# ==========================================================
# HOME PAGE
# ==========================================================

@app.route("/", methods=["GET", "POST"])
def home():

    # ------------------------------------------------------
    # OPEN WEBSITE / SHOW ONE-TIME RESULTS
    # ------------------------------------------------------

    if request.method == "GET":

        analysis_results = session.pop("analysis_results", None)

        if analysis_results:
            if "experience_analysis" not in analysis_results:
                return render_template("index.html")

            return render_template(
                "index.html",
                **analysis_results
            )

        return render_template("index.html")

    # ------------------------------------------------------
    # GET INPUTS
    # ------------------------------------------------------

    resume = request.files.get("resume")

    job_description = request.form.get(
        "job_description",
        ""
    )

    # ------------------------------------------------------
    # VALIDATE RESUME
    # ------------------------------------------------------

    if not resume or resume.filename == "":

        return render_template(
            "index.html",
            error="Please upload a resume PDF."
        )

    if not resume.filename.lower().endswith(".pdf"):

        return render_template(
            "index.html",
            error="Please upload a PDF resume only."
        )

    # ------------------------------------------------------
    # VALIDATE JOB DESCRIPTION
    # ------------------------------------------------------

    if not job_description.strip():

        return render_template(
            "index.html",
            error="Please enter a job description."
        )

    # ------------------------------------------------------
    # READ PDF
    # ------------------------------------------------------

    try:

        reader = PdfReader(resume)

        resume_text = ""

        for page in reader.pages:

            page_text = page.extract_text()

            if page_text:

                resume_text += page_text + "\n"

    except Exception as error:

        print("PDF ERROR:", error)

        return render_template(
            "index.html",
            error=(
                "Could not read the PDF file. "
                "Please upload a valid PDF."
            )
        )

    # ------------------------------------------------------
    # CHECK PDF TEXT
    # ------------------------------------------------------

    if not resume_text.strip():

        return render_template(
            "index.html",
            error=(
                "No readable text was found in this PDF. "
                "Please upload a text-based resume PDF."
            )
        )

    # ------------------------------------------------------
    # NORMALIZE TEXT
    # ------------------------------------------------------

    resume_text = normalize_text(resume_text)

    job_description = normalize_text(job_description)

    # ------------------------------------------------------
    # DETECT SKILLS
    # ------------------------------------------------------

    resume_skills = detect_skills(resume_text)

    job_skills = detect_skills(job_description)

    # ------------------------------------------------------
    # MATCHING SKILLS
    # ------------------------------------------------------

    matching_skills = []

    for skill in job_skills:

        if skill in resume_skills:

            matching_skills.append(skill)

    # ------------------------------------------------------
    # MISSING SKILLS
    # ------------------------------------------------------

    missing_skills = []

    for skill in job_skills:

        if skill not in resume_skills:

            missing_skills.append(skill)

    # ------------------------------------------------------
    # CALCULATE CURRENT SKILL SCORE
    # ------------------------------------------------------

    if job_skills:

        score = round(
            (len(matching_skills) / len(job_skills)) * 100
        )

    else:

        score = 0

    # ------------------------------------------------------
    # MATCH LEVEL
    # ------------------------------------------------------

    match_level, recommendation = get_match_information(score)

    # ------------------------------------------------------
    # EXTRACT EXPERIENCE
    # ------------------------------------------------------

    experiences = extract_experience(resume_text)

    experience_analysis = analyze_experience_requirement(
        job_description,
        experiences
    )

    # ------------------------------------------------------
    # TERMINAL OUTPUT
    # ------------------------------------------------------

    print()
    print("===================================")
    print("        RESUME ANALYSIS")
    print("===================================")

    print()
    print("Job Skills:")
    print(job_skills)

    print()
    print("Resume Skills:")
    print(resume_skills)

    print()
    print("Matching Skills:")
    print(matching_skills)

    print()
    print("Missing Skills:")
    print(missing_skills)

    print()
    print("Experience:")
    print(experiences)

    print()
    print("Match Score:", score, "%")

    print("Match Level:", match_level)

    print("===================================")
    print()

    # ------------------------------------------------------
    # SAVE RESULTS TEMPORARILY
    # ------------------------------------------------------

    session["analysis_results"] = {
        "score": score,
        "job_skills": job_skills,
        "resume_skills": resume_skills,
        "matching_skills": matching_skills,
        "missing_skills": missing_skills,
        "match_level": match_level,
        "recommendation": recommendation,
        "experiences": experiences,
        "experience_analysis": experience_analysis
    }

    # ------------------------------------------------------
    # REDIRECT AFTER ANALYSIS
    # ------------------------------------------------------

    return redirect(url_for("home"))


# ==========================================================
# START FLASK
# ==========================================================

if __name__ == "__main__":

    app.run(debug=True)


