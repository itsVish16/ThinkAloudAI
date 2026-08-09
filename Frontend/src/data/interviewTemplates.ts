export interface DialogueStep {
  id: string;
  speaker: 'ai' | 'user';
  message: string;
  triggerEvent?: string; // e.g. 'start', 'submit_code', 'next'
  status: 'pending' | 'active' | 'completed';
}

export interface InterviewTemplate {
  id: string;
  title: string;
  company: string;
  role: string;
  difficulty: 'Easy' | 'Medium' | 'Hard';
  durationMinutes: number;
  questionId: string; // references dsaQuestions
  topics: string[];
  stages: DialogueStep[];
}

export const interviewTemplates: InterviewTemplate[] = [
  {
    id: 'google-swe-two-sum',
    title: 'SWE II Technical Loop',
    company: 'Google',
    role: 'Software Engineer II',
    difficulty: 'Easy',
    durationMinutes: 45,
    questionId: 'two-sum',
    topics: ['Arrays', 'Hash Maps', 'Time Complexity'],
    stages: [
      {
        id: 'intro',
        speaker: 'ai',
        message: "Hello! Welcome to your Google Technical Mock Interview. My name is Alex, and I'll be your interviewer today. To get started, could you briefly introduce yourself and share what interests you about this role?",
        status: 'active'
      },
      {
        id: 'user-intro-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'problem-intro',
        speaker: 'ai',
        message: "Thank you for sharing! Let's jump into the coding question. I've shared the 'Two Sum' problem in your editor. Take a minute to read through it, and let me know how you plan to approach it before you start typing code.",
        status: 'pending'
      },
      {
        id: 'user-approach-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'coding-start',
        speaker: 'ai',
        message: "That approach sounds solid. The O(N) hash map solution is exactly what we want. Go ahead and start writing the code. Remember to talk through your lines so I can understand your thought process.",
        status: 'pending'
      },
      {
        id: 'user-coding-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'complexity-question',
        speaker: 'ai',
        message: "Great work, the solution compiles and all tests pass! Before we conclude, what is the exact space complexity of this code, and what would happen if the array was already sorted?",
        status: 'pending'
      },
      {
        id: 'user-complexity-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'outro',
        speaker: 'ai',
        message: "Excellent analysis. If it were sorted, we could indeed use a two-pointer approach for O(1) space. We are out of time, so I'll wrap it up here. I am running our evaluation agent and will display your grading scorecard now.",
        status: 'pending'
      }
    ]
  },
  {
    id: 'meta-frontend-lru',
    title: 'Senior Frontend Engineer Design & Coding',
    company: 'Meta',
    role: 'Senior Frontend Engineer',
    difficulty: 'Medium',
    durationMinutes: 60,
    questionId: 'lru-cache',
    topics: ['Design Patterns', 'Data Structures', 'LRU Cache'],
    stages: [
      {
        id: 'intro',
        speaker: 'ai',
        message: "Hi there, welcome! I'm Sarah from the Meta engineering team. In this mock interview, we'll design and build a Least Recently Used (LRU) cache. Before writing code, can you explain what caching eviction policies you know and why LRU is widely used?",
        status: 'active'
      },
      {
        id: 'user-intro-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'problem-intro',
        speaker: 'ai',
        message: "Good points! An LRU cache matches standard access patterns well. The problem detail is in your editor. Let's design the get and put methods to operate in O(1) time complexity. What data structure combinations will you use?",
        status: 'pending'
      },
      {
        id: 'user-approach-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'coding-start',
        speaker: 'ai',
        message: "Correct, a doubly-linked list combined with a hash map allows O(1) updates. Please begin your implementation. Ensure you handle the capacity constraints when eviction is triggered.",
        status: 'pending'
      },
      {
        id: 'user-coding-reply',
        speaker: 'user',
        message: "",
        status: 'pending'
      },
      {
        id: 'outro',
        speaker: 'ai',
        message: "Fantastic job implementing the nodes deletion and map sync. The code passes the test cases successfully. Let me close this session and summarize your score.",
        status: 'pending'
      }
    ]
  },
  {
    id: 'system-design-twitter',
    title: 'Distributed System Design',
    company: 'Amazon',
    role: 'Staff Software Engineer',
    difficulty: 'Hard',
    durationMinutes: 60,
    questionId: 'design-twitter',
    topics: ['System Design', 'Scalability', 'Microservices'],
    stages: [
      { id: 'intro', speaker: 'ai', message: "Welcome to the System Design round. Today, we're going to design a distributed system similar to Twitter. How would you approach the high-level architecture?", status: 'active' },
      { id: 'reply-1', speaker: 'user', message: "", status: 'pending' },
      { id: 'outro', speaker: 'ai', message: "Great thoughts on database sharding and caching. Let's wrap up.", status: 'pending' }
    ]
  },
  {
    id: 'lld-parking-lot',
    title: 'Low Level Design (LLD)',
    company: 'Microsoft',
    role: 'SDE II',
    difficulty: 'Medium',
    durationMinutes: 45,
    questionId: 'design-parking-lot',
    topics: ['LLD', 'OOD', 'Design Patterns'],
    stages: [
      { id: 'intro', speaker: 'ai', message: "Let's do an object-oriented design for a Parking Lot. What classes and interfaces would you define?", status: 'active' },
      { id: 'reply-1', speaker: 'user', message: "", status: 'pending' },
      { id: 'outro', speaker: 'ai', message: "Solid class hierarchy. Let's conclude the interview.", status: 'pending' }
    ]
  },
  {
    id: 'agentic-ai-engineer',
    title: 'Agentic AI Architecture',
    company: 'OpenAI',
    role: 'AI Engineer',
    difficulty: 'Hard',
    durationMinutes: 60,
    questionId: 'ai-agents',
    topics: ['Agentic AI', 'LLMs', 'Tool Calling'],
    stages: [
      { id: 'intro', speaker: 'ai', message: "Hello. We need to build an autonomous coding agent. How would you handle the observation and tool execution loops?", status: 'active' },
      { id: 'reply-1', speaker: 'user', message: "", status: 'pending' },
      { id: 'outro', speaker: 'ai', message: "Very comprehensive understanding of ReAct and tool calling.", status: 'pending' }
    ]
  },
  {
    id: 'ml-engineer-infra',
    title: 'ML Engineering & MLOps',
    company: 'Netflix',
    role: 'Machine Learning Engineer',
    difficulty: 'Medium',
    durationMinutes: 45,
    questionId: 'ml-infra',
    topics: ['ML Engineer', 'Model Serving', 'Data Pipelines'],
    stages: [
      { id: 'intro', speaker: 'ai', message: "Welcome. How would you design a real-time recommendation model serving pipeline that handles 100k RPS?", status: 'active' },
      { id: 'reply-1', speaker: 'user', message: "", status: 'pending' },
      { id: 'outro', speaker: 'ai', message: "Good explanation of feature stores and model registries.", status: 'pending' }
    ]
  },
  {
    id: 'behavioural-leadership',
    title: 'Behavioural & Leadership',
    company: 'Apple',
    role: 'Engineering Manager',
    difficulty: 'Medium',
    durationMinutes: 45,
    questionId: 'behavioural',
    topics: ['Behavioural', 'Leadership', 'Conflict Resolution'],
    stages: [
      { id: 'intro', speaker: 'ai', message: "Tell me about a time you had to resolve a conflict between two senior engineers on your team.", status: 'active' },
      { id: 'reply-1', speaker: 'user', message: "", status: 'pending' },
      { id: 'outro', speaker: 'ai', message: "Thank you for sharing your experience.", status: 'pending' }
    ]
  },
  {
    id: 'hr-manager-round',
    title: 'HR Manager Round',
    company: 'Stripe',
    role: 'Any Role',
    difficulty: 'Easy',
    durationMinutes: 30,
    questionId: 'hr-culture',
    topics: ['HR manager round', 'Culture Fit', 'Motivation'],
    stages: [
      { id: 'intro', speaker: 'ai', message: "Hi! Why do you want to join our company, and where do you see yourself in 3 years?", status: 'active' },
      { id: 'reply-1', speaker: 'user', message: "", status: 'pending' },
      { id: 'outro', speaker: 'ai', message: "Great chatting with you! We'll be in touch.", status: 'pending' }
    ]
  }
];
