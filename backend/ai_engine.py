import random

# Blueprints
TECHNICAL_BLUEPRINT = [
    "Programming Fundamentals",
    "Data Structures / Algorithms",
    "OOP / Programming Concepts",
    "DBMS / SQL",
    "Operating Systems / Computer Fundamentals",
    "Problem Solving",
    "Project / Practical Experience",
    "Debugging / Technical Scenario",
    "Applied Technical Reasoning",
    "Advanced Technical / Role-Oriented Question"
]

TECHNICAL_QUESTIONS = {
    0: ["What is the difference between a compiled and an interpreted language?", "Can you explain the concept of variables and data types in programming?", "How does memory management work in modern programming languages?"],
    1: ["Can you explain how a hash table works under the hood?", "What is the difference between a stack and a queue?", "How would you find the shortest path in a graph?"],
    2: ["What are the four main principles of Object-Oriented Programming?", "Can you explain the difference between abstract classes and interfaces?", "What is polymorphism and how is it useful?"],
    3: ["What is the difference between SQL and NoSQL databases?", "Can you explain ACID properties in DBMS?", "How do database indexes work to speed up queries?"],
    4: ["What is the difference between a process and a thread?", "Can you explain what virtual memory is?", "How does an operating system handle deadlocks?"],
    5: ["Describe your approach when faced with a complex technical problem you haven't seen before.", "How do you optimize a piece of code that is running too slow?", "Walk me through how you would design a URL shortener."],
    6: ["Tell me about a technical project you built and the architecture you chose.", "What was the most challenging bug you encountered in a recent project and how did you fix it?", "Describe a time you had to learn a new technology quickly for a project."],
    7: ["You have an application that crashes randomly in production. How do you debug it?", "If a database query suddenly becomes very slow, what steps would you take to investigate?", "How would you handle a memory leak in your application?"],
    8: ["Why might you choose a microservices architecture over a monolithic one?", "When would you choose to use caching, and what are the trade-offs?", "How do you ensure your code is secure against common vulnerabilities?"],
    9: ["What is a recent advancement in your technical domain that you are excited about?", "How do you balance writing perfect code versus delivering a product on time?", "Where do you see the future of software development heading?"]
}

HR_BLUEPRINT = [
    "Self Introduction",
    "Strengths",
    "Weakness / Area of Improvement",
    "Teamwork",
    "Conflict Handling",
    "Leadership / Initiative",
    "Failure / Learning Experience",
    "Handling Pressure / Difficult Situations",
    "Career Goals / Motivation",
    "Situational HR Question"
]

HR_QUESTIONS = {
    0: ["Tell me about yourself.", "Could you walk me through your background and experiences?", "How would you describe yourself professionally?"],
    1: ["What is one strength that helps you perform well?", "What do you consider your greatest professional strength?", "Why should we hire you based on your strengths?"],
    2: ["Tell me about a weakness you are actively improving.", "What is one area of your professional skills that needs improvement?", "Can you share a time when you realized you needed to improve in a certain area?"],
    3: ["Describe a time when you worked in a successful team.", "How do you contribute to a team environment?", "Tell me about a time you had to rely on a team member to accomplish a goal."],
    4: ["Describe a time when you worked with a difficult team member.", "How do you handle disagreements in the workplace?", "Tell me about a time you had a conflict with a colleague and how you resolved it."],
    5: ["Tell me about a time you took the initiative on a project.", "Describe a situation where you had to lead a group.", "How do you motivate others when team morale is low?"],
    6: ["Tell me about a failure and what you learned from it.", "Describe a time when things did not go as planned.", "What is the biggest mistake you've made professionally and how did you recover?"],
    7: ["How do you handle pressure when multiple tasks have to be completed?", "Describe a stressful situation at work and how you managed it.", "How do you prioritize your work when everything seems urgent?"],
    8: ["Where do you see yourself in five years?", "What motivates you to do your best work?", "What are your long-term career goals?"],
    9: ["If you realized you couldn't meet a deadline, what would you do?", "How would you handle a situation where you were asked to do something unethical?", "What would you do if you were assigned a task you didn't know how to complete?"]
}

GENERAL_BLUEPRINT = [
    "General Introduction / Background",
    "General Awareness",
    "Technology / Society",
    "Logical Thinking",
    "Problem Solving",
    "Current or General Topic",
    "Opinion-Based Reasoning",
    "Situational Scenario",
    "Communication / Explanation",
    "Open Discussion / Reasoning"
]

GENERAL_QUESTIONS = {
    0: ["Could you introduce yourself and share a bit about your background?", "Tell me about your journey so far and what led you here.", "What are your primary interests and hobbies?"],
    1: ["What is one major global event recently that caught your attention?", "How do you stay updated with current events?", "What do you think is a significant trend in the world right now?"],
    2: ["What recent technology interests you and why?", "How do you think artificial intelligence will change everyday life?", "What is one negative impact of social media and how can we mitigate it?"],
    3: ["If you had to choose between being perfect and late, or good and on time, which would you choose and why?", "How do you approach making a difficult decision?", "Can you give an example of a time you used logic to solve a problem?"],
    4: ["How would you solve a common problem in your college or workplace?", "Describe a time you found a creative solution to an everyday problem.", "What steps do you take when you are completely stuck on a problem?"],
    5: ["What do you think is one major challenge young professionals face today?", "How has remote work changed the way people collaborate?", "What is your opinion on the importance of continuous learning?"],
    6: ["Do you believe hard work or talent is more important for success?", "What is one change you would make to improve your community?", "Is it better to be a specialist or a generalist in today's world?"],
    7: ["If you saw a colleague struggling with their workload, what would you do?", "Imagine you are given a task with no clear instructions. What is your first step?", "How would you handle a sudden change in plans that ruins your schedule?"],
    8: ["If you had to explain a complex topic to someone with no technical background, how would you do it?", "Describe how you would teach a child to tie their shoes.", "Why is clear communication important in daily life?"],
    9: ["What is a book, movie, or idea that completely changed your perspective?", "If you could change one thing about the education system, what would it be?", "What advice would you give to someone just starting their career?"]
}

def generate_next_question(division: str, question_number: int, previous_questions: list, candidate_profile: dict, difficulty: str = "Medium") -> str:
    """
    Generates the next question based on the division blueprint.
    question_number is 1-indexed (1 to 10).
    """
    idx = question_number - 1
    if idx < 0 or idx > 9:
        idx = 0
        
    div_lower = division.lower()
    
    if div_lower == "technical":
        pool = TECHNICAL_QUESTIONS.get(idx, TECHNICAL_QUESTIONS[0])
    elif div_lower == "hr":
        pool = HR_QUESTIONS.get(idx, HR_QUESTIONS[0])
    elif div_lower == "general":
        pool = GENERAL_QUESTIONS.get(idx, GENERAL_QUESTIONS[0])
    else:
        pool = GENERAL_QUESTIONS.get(idx, GENERAL_QUESTIONS[0])
        
    # Simple simulated AI: pick a question from the pool that hasn't been asked yet
    available_questions = [q for q in pool if q not in previous_questions]
    
    if not available_questions:
        # Fallback if all somehow used (unlikely with strict ordering)
        available_questions = pool
        
    return random.choice(available_questions)