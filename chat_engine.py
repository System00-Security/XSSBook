"""
XSSBook Chat Engine - ML-based response system for dummy users
Contains intentional XSS vulnerabilities for educational purposes
"""
import random
import re
from datetime import datetime

class ChatEngine:
    def __init__(self):
        # Greeting patterns and responses
        self.greeting_patterns = {
            r'\b(hi|hello|hey|greetings|good morning|good afternoon|good evening)\b': [
                "Hey there! 😊 How's your day going?",
                "Hello! Great to see you online! What's up?",
                "Hi! Hope you're having an awesome day!",
                "Hey! What brings you here today?",
                "Hello friend! How are you doing?",
                "Hi there! Nice to chat with you!",
                "Hey! What's new with you?",
                "Hello! Ready for some interesting conversation?",
                "Hey! Good to see you here! 😊",
                "Hi! How are you doing today?",
            ],
            r'\b(how are you|how\'s it going|what\'s up|whats up)\b': [
                "I'm doing great, thanks for asking! How about you?",
                "Pretty good! Just enjoying some social networking time 😄",
                "All good here! What's been keeping you busy?",
                "I'm fantastic! Hope you're having a wonderful day too!",
                "Doing well! Any exciting plans for today?",
                "Great! Just chatting with friends online. You?",
                "I'm good! What's your favorite thing about XSSBook?",
                "Awesome! How are you doing?",
                "I'm great! And you?",
            ]
        }
        
        # Topic-based responses
        self.topic_responses = {
            # Social media and technology
            r'\b(social media|facebook|instagram|twitter|tech|technology|app|website)\b': [
                "I love discussing technology! Social media has really changed how we connect.",
                "Tech is fascinating! What's your favorite social platform?",
                "XSSBook is pretty cool, right? I enjoy the community here!",
                "Social media can be both amazing and overwhelming sometimes.",
                "Technology keeps evolving so fast! It's exciting to be part of it.",
                "Yeah, social media is great for connecting with people!",
                "I agree! Technology is amazing and keeps advancing!",
            ],
            
            # Hobbies and interests
            r'\b(hobby|hobbies|interest|love|enjoy|like|favorite|music|movies|books|sports|games)\b': [
                "That sounds interesting! I love hearing about people's passions.",
                "Hobbies are so important for a balanced life! What do you enjoy most?",
                "I'm into photography and reading. What about you?",
                "Music is life! What genre do you listen to?",
                "Movies are great for unwinding. Any recent favorites?",
                "Sports can be so exciting! Do you play or just watch?",
                "Gaming is awesome! I love both classic and modern games.",
                "Reading opens up whole new worlds! Any book recommendations?",
                "That's a cool hobby! I'd love to hear more about it.",
                "Nice! I share similar interests!",
            ],
            
            # Work and career
            r'\b(work|job|career|office|business|project|study|school|college|university)\b': [
                "Work-life balance is so important! How do you manage it?",
                "Career growth is exciting! What field are you in?",
                "Projects can be challenging but rewarding. What are you working on?",
                "Education is a lifelong journey! Always something new to learn.",
                "School days... some of the best memories! What did you study?",
                "Professional development is key in today's world.",
                "Office culture varies so much between companies!",
                "Work sounds interesting! Tell me more about what you do.",
                "Career talk! I'd love to hear about your experiences!",
            ],
            
            # Food and lifestyle
            r'\b(food|eat|cooking|restaurant|recipe|coffee|drink|travel|vacation|weekend)\b': [
                "Food is one of life's greatest pleasures! What's your favorite cuisine?",
                "I love trying new recipes! Any cooking tips?",
                "Coffee is essential for my day! Are you a coffee person too?",
                "Travel broadens the mind! Any dream destinations?",
                "Weekends are for recharging! How do you like to spend yours?",
                "Good food and good company make the best combinations!",
                "Cooking can be so therapeutic and creative!",
                "Restaurant discoveries are always exciting!",
                "I love food discussions! What's your favorite type of cuisine?",
                "Yummy! What's your favorite dish to cook?",
            ],
            
            # Weather and general
            r'\b(weather|hot|cold|rain|sunny|cloudy|beautiful|nice|day|today|tomorrow)\b': [
                "Weather definitely affects the mood! How's it where you are?",
                "Beautiful days are perfect for outdoor activities!",
                "I love when the weather is just right - not too hot, not too cold.",
                "Rainy days are perfect for staying in and chatting online!",
                "Sunny weather always puts me in a good mood! ☀️",
                "Weather can be so unpredictable these days!",
                "Hope you're having a lovely day regardless of the weather!",
                "Nice weather we're having! How's it where you are?",
                "Great day! How's the weather there?",
            ]
        }
        
        # Question responses
        self.question_responses = [
            "That's a great question! What do you think about it?",
            "Interesting point! I'd love to hear your perspective on this.",
            "Hmm, that makes me think... What's your take?",
            "Good question! It really depends on the situation, don't you think?",
            "I've been wondering about that too! Any insights?",
            "That's thought-provoking! How would you approach it?",
            "Great minds think alike! What's your opinion?",
            "That's a good question! I'm curious about your thoughts.",
            "Interesting! What do you think about it?",
        ]
        
        # Compliment responses
        self.compliment_patterns = {
            r'\b(nice|good|great|awesome|amazing|cool|sweet|perfect|excellent|wonderful)\b': [
                "Thank you! That's so kind of you to say! 😊",
                "Aww, you're too sweet! Thanks!",
                "I appreciate that! You seem pretty awesome yourself!",
                "That means a lot coming from you! Thanks!",
                "You're so nice! Thank you for the kind words!",
                "Thanks! You just made my day brighter! ✨",
                "That's really thoughtful of you to say!",
                "Thank you so much! That's really nice!",
                "Thanks! You're sweet too!",
            ]
        }
        
        # Emotional support responses
        self.support_patterns = {
            r'\b(sad|tired|stressed|worried|anxious|difficult|hard|problem|issue)\b': [
                "I'm sorry to hear that. Want to talk about what's bothering you?",
                "That sounds tough. Sometimes it helps just to share what's on your mind.",
                "I understand that can be challenging. You're not alone in feeling this way.",
                "Difficult times happen to everyone. What usually helps you feel better?",
                "That must be stressful. Have you tried any relaxation techniques?",
                "I hear you. Sometimes talking through problems can provide clarity.",
                "It's okay to feel overwhelmed sometimes. Take it one step at a time.",
                "I'm here if you need to talk about it.",
                "Sorry to hear that! Want to chat about what's going on?",
            ]
        }
        
        # Fallback responses for unmatched messages
        self.fallback_responses = [
            "That's interesting! Tell me more about that.",
            "I see what you mean! What made you think of that?",
            "Cool! I'd love to hear more about your thoughts on this.",
            "That sounds intriguing! Can you elaborate?",
            "Interesting perspective! What's your experience with that?",
            "I hadn't thought of it that way before! Thanks for sharing.",
            "That's a unique point of view! What else do you think about it?",
            "Thanks for sharing that! It's always nice to learn something new.",
            "I appreciate you telling me that! What else is on your mind?",
            "That's pretty cool! Any other thoughts you'd like to share?",
            "Fascinating! I enjoy our conversations.",
            "Thanks for that insight! You always have interesting things to say.",
            "I like how you think! What else would you like to chat about?",
            "That's thoughtful! I value our discussions.",
            "Interesting! Tell me more about your thoughts on that!",
            "Cool! What else is new with you?",
            "Nice! Any other thoughts you'd like to share?",
        ]
        
        # Time-based responses
        self.time_responses = {
            'morning': [
                "Good morning! Hope you have a fantastic day ahead! ☀️",
                "Morning! Ready to tackle the day?",
                "Good morning! What's the plan for today?",
                "Good morning! Hope you're having a great start to your day! ☀️",
            ],
            'afternoon': [
                "Good afternoon! How's your day going so far?",
                "Afternoon! Hope you're having a productive day!",
                "Good afternoon! Taking a break from the day?",
                "Good afternoon! How has your day been treating you?",
            ],
            'evening': [
                "Good evening! How was your day?",
                "Evening! Time to unwind and relax!",
                "Good evening! What's the highlight of your day?",
                "Good evening! Hope you had a wonderful day!",
            ]
        }
    
    def get_response(self, message, user_name="friend"):
        """
        Generate an ML-like response based on the input message
        Contains intentional XSS vulnerabilities for educational purposes
        """
        message_lower = message.lower().strip()
        
        # Check for greetings
        for pattern, responses in self.greeting_patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return random.choice(responses)
        
        # Check for compliments
        for pattern, responses in self.compliment_patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return random.choice(responses)
        
        # Check for emotional support needs
        for pattern, responses in self.support_patterns.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return random.choice(responses)
        
        # Check for topic-based responses
        for pattern, responses in self.topic_responses.items():
            if re.search(pattern, message_lower, re.IGNORECASE):
                return random.choice(responses)
        
        # Check for questions (ending with ?)
        if message.strip().endswith('?'):
            return random.choice(self.question_responses)
        
        # Time-based responses
        current_hour = datetime.now().hour
        if 5 <= current_hour < 12:
            time_period = 'morning'
        elif 12 <= current_hour < 17:
            time_period = 'afternoon'
        else:
            time_period = 'evening'
        
        # Random chance to give time-based response
        if random.random() < 0.1:  # 10% chance
            return random.choice(self.time_responses[time_period])
        
        # Fallback response
        response = random.choice(self.fallback_responses)
        
        # Add user name occasionally for personalization
        if random.random() < 0.3 and user_name != "friend":  # 30% chance
            response = f"{response} {user_name}!"
        
        return response
    
    def get_conversation_starter(self):
        """Get a conversation starter for new chats"""
        starters = [
            "Hey! How's everything going with you?",
            "Hi there! What's been keeping you busy lately?",
            "Hello! Nice to see you on XSSBook! What's new?",
            "Hey! Hope you're having a great day! What's up?",
            "Hi! Just wanted to say hello and see how you're doing!",
            "Hello! What's the most interesting thing that happened to you today?",
            "Hey! Any exciting plans for the weekend?",
            "Hey! How are you doing today?",
            "Hi! What's new with you lately?",
        ]
        return random.choice(starters)

# Global chat engine instance
chat_engine = ChatEngine()
