"""
app/db/seed.py
--------------
Seeds the database with 5 DS/AI-ML courses, lessons, and questions.

RUN ONCE after starting the server for the first time:
    cd backend
    python app/db/seed.py

Safe to re-run — checks if data already exists before inserting.
"""

import asyncio
import sys
import os

# Add backend/ to Python path so imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import AsyncSessionLocal, create_tables
from app.models.user import User, FaceEncoding          # noqa
from app.models.course import Course, Lesson, LessonProgress  # noqa
from app.models.assessment import Assessment, Question, Result  # noqa
from app.models.analytics import Analytics, ActivityLog  # noqa
from sqlalchemy import select


# ── Seed data definitions ──────────────────────────────────────────────────

COURSES = [
    {
        "title": "Python for Data Science",
        "description": "Master Python fundamentals for data analysis — NumPy, Pandas, and Matplotlib.",
        "subject": "Python",
        "difficulty": 1,
    },
    {
        "title": "Machine Learning Fundamentals",
        "description": "Understand supervised and unsupervised learning algorithms from scratch.",
        "subject": "Machine Learning",
        "difficulty": 2,
    },
    {
        "title": "Deep Learning & Neural Networks",
        "description": "Build neural networks, CNNs, and RNNs using modern frameworks.",
        "subject": "Deep Learning",
        "difficulty": 3,
    },
    {
        "title": "Natural Language Processing",
        "description": "Text processing, transformers, and large language model concepts.",
        "subject": "NLP",
        "difficulty": 3,
    },
    {
        "title": "Data Analysis & Statistics",
        "description": "Statistical foundations, hypothesis testing, and data visualization.",
        "subject": "Statistics",
        "difficulty": 1,
    },
]

LESSONS = {
    "Python for Data Science": [
        ("Introduction to NumPy", "NumPy is the foundation of data science in Python...\n\n## Arrays\nA NumPy array is a grid of values, all of the same type.\n```python\nimport numpy as np\narr = np.array([1, 2, 3, 4, 5])\nprint(arr.shape)  # (5,)\n```\n\n## Key Operations\n- `np.zeros(shape)` — create array of zeros\n- `np.ones(shape)` — create array of ones\n- `arr.reshape(rows, cols)` — reshape array\n- `arr.mean()`, `arr.std()` — statistics", 1, "text"),
        ("Pandas DataFrames", "Pandas provides DataFrame — a 2D labeled data structure.\n\n## Creating DataFrames\n```python\nimport pandas as pd\ndf = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})\n```\n\n## Essential Operations\n- `df.head()` — first 5 rows\n- `df.describe()` — summary statistics\n- `df['col']` — select column\n- `df.dropna()` — remove missing values\n- `df.groupby('col').mean()` — group and aggregate", 2, "text"),
        ("Data Visualization with Matplotlib", "Matplotlib is Python's primary plotting library.\n\n## Basic Plot\n```python\nimport matplotlib.pyplot as plt\nplt.plot([1,2,3], [4,5,6])\nplt.title('My Chart')\nplt.show()\n```\n\n## Chart Types\n- `plt.plot()` — line chart\n- `plt.bar()` — bar chart\n- `plt.scatter()` — scatter plot\n- `plt.hist()` — histogram", 3, "text"),
        ("Data Cleaning Techniques", "Real-world data is messy. Data cleaning is 80% of data science.\n\n## Common Issues\n- Missing values (`NaN`)\n- Duplicate rows\n- Wrong data types\n- Outliers\n\n## Solutions\n```python\ndf.isnull().sum()       # count missing\ndf.fillna(0)            # fill with 0\ndf.dropna()             # drop rows\ndf.drop_duplicates()    # remove dupes\ndf['age'] = df['age'].astype(int)  # fix type\n```", 4, "text"),
    ],
    "Machine Learning Fundamentals": [
        ("What is Machine Learning?", "Machine Learning is teaching computers to learn from data without explicit programming.\n\n## Three Types\n1. **Supervised Learning** — labelled data, predict output\n2. **Unsupervised Learning** — find hidden patterns\n3. **Reinforcement Learning** — learn from rewards\n\n## The ML Workflow\n1. Collect data\n2. Preprocess\n3. Choose model\n4. Train\n5. Evaluate\n6. Deploy", 1, "text"),
        ("Linear Regression", "Linear Regression predicts a continuous value by fitting a line.\n\n## Formula\n`y = mx + b`\nwhere m=slope, b=intercept\n\n## In Python\n```python\nfrom sklearn.linear_model import LinearRegression\nmodel = LinearRegression()\nmodel.fit(X_train, y_train)\npredictions = model.predict(X_test)\n```\n\n## Evaluation\n- MSE (Mean Squared Error)\n- R² Score (1.0 = perfect)", 2, "text"),
        ("Classification Algorithms", "Classification predicts which category an input belongs to.\n\n## Algorithms\n- **Logistic Regression** — binary classification\n- **Decision Trees** — rule-based splitting\n- **Random Forest** — ensemble of trees\n- **SVM** — maximum margin classifier\n- **KNN** — nearest neighbours\n\n## Metrics\n- Accuracy, Precision, Recall, F1-Score\n- Confusion Matrix\n- ROC-AUC Curve", 3, "text"),
        ("Model Evaluation & Overfitting", "A model that memorises training data fails on new data — this is overfitting.\n\n## Train/Test Split\n```python\nfrom sklearn.model_selection import train_test_split\nX_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)\n```\n\n## Cross-Validation\n```python\nfrom sklearn.model_selection import cross_val_score\nscores = cross_val_score(model, X, y, cv=5)\n```\n\n## Regularisation\n- L1 (Lasso) — feature selection\n- L2 (Ridge) — weight shrinkage", 4, "text"),
    ],
    "Deep Learning & Neural Networks": [
        ("Neural Network Basics", "A neural network is a system of layers of interconnected nodes (neurons).\n\n## Architecture\n- **Input layer** — receives features\n- **Hidden layers** — learn representations\n- **Output layer** — produces prediction\n\n## Activation Functions\n- ReLU: `max(0, x)` — most common\n- Sigmoid: `1/(1+e^-x)` — binary output\n- Softmax — multi-class output\n\n## Training\nBackpropagation + Gradient Descent adjust weights to minimise loss.", 1, "text"),
        ("Convolutional Neural Networks", "CNNs are specialised for image data.\n\n## Key Layers\n- **Conv2D** — detects features (edges, textures)\n- **MaxPooling** — reduces dimensions\n- **Flatten** — converts to 1D\n- **Dense** — classification\n\n```python\nfrom tensorflow.keras import layers\nmodel = tf.keras.Sequential([\n    layers.Conv2D(32, (3,3), activation='relu'),\n    layers.MaxPooling2D(),\n    layers.Flatten(),\n    layers.Dense(10, activation='softmax')\n])\n```", 2, "text"),
        ("Recurrent Neural Networks", "RNNs process sequential data — text, time series, speech.\n\n## LSTM\nLong Short-Term Memory solves the vanishing gradient problem.\n\n```python\nmodel = tf.keras.Sequential([\n    layers.LSTM(64, return_sequences=True),\n    layers.LSTM(32),\n    layers.Dense(1)\n])\n```\n\n## Use Cases\n- Text generation\n- Sentiment analysis\n- Time series prediction\n- Speech recognition", 3, "text"),
        ("Transfer Learning", "Use a pre-trained model as a starting point instead of training from scratch.\n\n## Why?\n- Pre-trained on millions of images\n- Saves time and compute\n- Works well with small datasets\n\n## Example\n```python\nbase = tf.keras.applications.MobileNetV2(weights='imagenet', include_top=False)\nbase.trainable = False  # freeze weights\nmodel = tf.keras.Sequential([base, layers.Dense(num_classes)])\n```", 4, "text"),
    ],
    "Natural Language Processing": [
        ("Text Preprocessing", "Before feeding text to ML models, we must clean and tokenize it.\n\n## Steps\n1. Lowercase\n2. Remove punctuation\n3. Tokenize (split into words)\n4. Remove stopwords\n5. Stemming / Lemmatization\n\n```python\nimport nltk\nfrom nltk.tokenize import word_tokenize\ntokens = word_tokenize('Hello world!')\n# ['Hello', 'world', '!']\n```", 1, "text"),
        ("Word Embeddings", "Word embeddings represent words as dense vectors that capture meaning.\n\n## Word2Vec\nWords with similar meanings have similar vectors.\n`king - man + woman ≈ queen`\n\n## Types\n- Word2Vec (Google)\n- GloVe (Stanford)\n- FastText (Facebook)\n\n```python\nfrom gensim.models import Word2Vec\nmodel = Word2Vec(sentences, vector_size=100, window=5)\nvector = model.wv['python']\n```", 2, "text"),
        ("Transformers & Attention", "Transformers revolutionised NLP with self-attention mechanism.\n\n## Key Idea\nInstead of reading left-to-right, attention allows each word to look at ALL other words simultaneously.\n\n## BERT\nBidirectional Encoder from Transformers — reads context from both directions.\n\n## GPT\nGenerative Pre-trained Transformer — predicts next token.\n\n## HuggingFace\n```python\nfrom transformers import pipeline\nclassifier = pipeline('sentiment-analysis')\nresult = classifier('I love data science!')\n```", 3, "text"),
        ("Large Language Models", "LLMs like GPT-4 are trained on vast text corpora to understand and generate human language.\n\n## Key Concepts\n- **Tokens** — chunks of text (words/subwords)\n- **Context window** — how much text the model sees\n- **Temperature** — controls randomness\n- **Prompt engineering** — craft inputs for better outputs\n\n## APIs\n```python\nfrom openai import OpenAI\nclient = OpenAI()\nresponse = client.chat.completions.create(\n    model='gpt-4o-mini',\n    messages=[{'role': 'user', 'content': 'Explain NLP'}]\n)\n```", 4, "text"),
    ],
    "Data Analysis & Statistics": [
        ("Descriptive Statistics", "Descriptive statistics summarise and describe data.\n\n## Measures of Central Tendency\n- **Mean** — average: `sum(x) / n`\n- **Median** — middle value\n- **Mode** — most frequent value\n\n## Measures of Spread\n- **Variance** — average squared deviation\n- **Standard Deviation** — sqrt(variance)\n- **IQR** — Q3 - Q1\n\n```python\nimport numpy as np\ndata = [1, 2, 3, 4, 5]\nprint(np.mean(data), np.std(data))\n```", 1, "text"),
        ("Probability Distributions", "Probability distributions describe how likely each outcome is.\n\n## Common Distributions\n- **Normal** — bell curve, mean±std\n- **Binomial** — success/failure trials\n- **Poisson** — count of events\n- **Uniform** — equal probability\n\n```python\nfrom scipy import stats\nimport numpy as np\n# Normal distribution\nsamples = np.random.normal(loc=0, scale=1, size=1000)\n# Test normality\nstat, p = stats.shapiro(samples)\n```", 2, "text"),
        ("Hypothesis Testing", "Hypothesis testing determines if an observation is statistically significant.\n\n## Process\n1. State H₀ (null hypothesis) and H₁ (alternative)\n2. Choose significance level α (usually 0.05)\n3. Calculate test statistic\n4. Compute p-value\n5. If p < α → reject H₀\n\n## Common Tests\n- **t-test** — compare means\n- **Chi-square** — categorical relationships\n- **ANOVA** — compare multiple groups", 3, "text"),
        ("Correlation & Regression Analysis", "Correlation measures the relationship between two variables.\n\n## Pearson Correlation\nRange: -1 to +1\n- +1 = perfect positive\n- 0 = no correlation\n- -1 = perfect negative\n\n```python\nimport pandas as pd\nimport seaborn as sns\n# Correlation matrix\ncorr = df.corr()\nsns.heatmap(corr, annot=True)\n```\n\n## Causation ≠ Correlation\nTwo variables can be correlated without one causing the other.", 4, "text"),
    ],
}

QUESTIONS = {
    "Python for Data Science": [
        # EASY
        ("What does NumPy stand for?", ["A) Numerical Python", "B) New Python", "C) Numpy Unity", "D) None of these"], "A) Numerical Python", "easy", "numpy", "NumPy stands for Numerical Python, a library for numerical computing."),
        ("Which method shows the first 5 rows of a DataFrame?", ["A) df.head()", "B) df.first()", "C) df.top()", "D) df.show()"], "A) df.head()", "easy", "pandas", "df.head() returns the first N rows (default 5)."),
        ("How do you import Pandas?", ["A) import pd", "B) import pandas as pd", "C) from pandas import *", "D) import pandas"], "B) import pandas as pd", "easy", "pandas", "The convention is: import pandas as pd"),
        ("What shape does a 1D NumPy array have?", ["A) (n,)", "B) (n, 1)", "C) (1, n)", "D) [n]"], "A) (n,)", "easy", "numpy", "A 1D array with n elements has shape (n,)."),
        ("Which function creates a NumPy array of zeros?", ["A) np.empty()", "B) np.zero()", "C) np.zeros()", "D) np.null()"], "C) np.zeros()", "easy", "numpy", "np.zeros(shape) creates an array filled with 0.0."),
        ("What does df.describe() do?", ["A) Shows column names", "B) Shows data types", "C) Shows summary statistics", "D) Shows first 5 rows"], "C) Shows summary statistics", "easy", "pandas", "df.describe() shows count, mean, std, min, quartiles, max."),
        # MEDIUM
        ("What is the output of np.array([1,2,3]).reshape(3,1).shape?", ["A) (3,)", "B) (1, 3)", "C) (3, 1)", "D) (3,3)"], "C) (3, 1)", "medium", "numpy", "reshape(3,1) creates a column vector with shape (3, 1)."),
        ("Which Pandas method removes duplicate rows?", ["A) df.unique()", "B) df.drop_duplicates()", "C) df.remove_dupes()", "D) df.distinct()"], "B) df.drop_duplicates()", "medium", "data_cleaning", "df.drop_duplicates() removes duplicate rows from a DataFrame."),
        ("What does df.groupby('col').mean() compute?", ["A) Mean of entire DataFrame", "B) Mean for each unique value in col", "C) Mean of col only", "D) Nothing"], "B) Mean for each unique value in col", "medium", "pandas", "groupby splits data by unique values, then mean() computes the average for each group."),
        ("How do you select rows where age > 30 in Pandas?", ["A) df.where(age > 30)", "B) df[df['age'] > 30]", "C) df.filter(age > 30)", "D) df.select(age > 30)"], "B) df[df['age'] > 30]", "medium", "pandas", "Boolean indexing: df[condition] selects rows where condition is True."),
        # HARD
        ("What does np.einsum('ij,jk->ik', A, B) compute?", ["A) Element-wise product", "B) Matrix multiplication", "C) Dot product of vectors", "D) Transpose"], "B) Matrix multiplication", "hard", "numpy", "einsum with 'ij,jk->ik' performs standard matrix multiplication."),
        ("Which method handles missing values by forward-filling?", ["A) df.fillna(method='ffill')", "B) df.fill_forward()", "C) df.pad()", "D) A and C"], "D) A and C", "hard", "data_cleaning", "Both df.fillna(method='ffill') and df.pad() forward-fill missing values."),
    ],
    "Machine Learning Fundamentals": [
        ("What type of problem is predicting house prices?", ["A) Classification", "B) Clustering", "C) Regression", "D) Reinforcement"], "C) Regression", "easy", "linear_regression", "Predicting a continuous value (price) is a regression problem."),
        ("Which algorithm uses 'distance to nearest neighbours'?", ["A) SVM", "B) KNN", "C) Decision Tree", "D) Naive Bayes"], "B) KNN", "easy", "classification", "K-Nearest Neighbours classifies based on the majority class among K closest points."),
        ("What is overfitting?", ["A) Model too simple for data", "B) Model memorises training data, fails on new data", "C) Model trained too quickly", "D) Too much training data"], "B) Model memorises training data, fails on new data", "easy", "model_evaluation", "Overfitting: high training accuracy, low test accuracy — model memorised instead of learning patterns."),
        ("What does R² = 1.0 mean?", ["A) Model is wrong", "B) Model explains 100% of variance", "C) Overfitting", "D) Data is perfect"], "B) Model explains 100% of variance", "easy", "linear_regression", "R²=1.0 means the model perfectly predicts the target variable."),
        ("What is cross-validation used for?", ["A) Speed up training", "B) Reliable model evaluation using all data", "C) Feature selection", "D) Data augmentation"], "B) Reliable model evaluation using all data", "medium", "model_evaluation", "Cross-validation splits data into K folds and evaluates K times for more reliable performance estimates."),
        ("What does L1 regularisation (Lasso) do to weights?", ["A) Doubles all weights", "B) Shrinks weights toward zero, can make them exactly zero", "C) Normalises weights", "D) Removes bias"], "B) Shrinks weights toward zero, can make them exactly zero", "medium", "model_evaluation", "L1 regularisation adds sum of absolute weights to loss, driving some weights to exactly 0 (feature selection)."),
        ("Which metric is best for imbalanced classification?", ["A) Accuracy", "B) F1-Score", "C) MSE", "D) R²"], "B) F1-Score", "medium", "model_evaluation", "F1-Score balances Precision and Recall, making it better for imbalanced datasets where accuracy is misleading."),
        ("What is the kernel trick in SVM?", ["A) A fast training algorithm", "B) Maps data to higher dimensions without computing the transformation explicitly", "C) Selects support vectors", "D) Normalises the margin"], "B) Maps data to higher dimensions without computing the transformation explicitly", "hard", "classification", "The kernel trick computes dot products in a high-dimensional space efficiently, enabling non-linear classification."),
        ("In Random Forest, what is bagging?", ["A) Removing features", "B) Training each tree on a random subset of training data with replacement", "C) Combining tree outputs by voting", "D) Pruning trees"], "B) Training each tree on a random subset of training data with replacement", "hard", "classification", "Bootstrap Aggregating (bagging) trains each tree on a random sample (with replacement) to reduce variance."),
        ("What is the bias-variance tradeoff?", ["A) More complex model → lower bias, higher variance", "B) More data always reduces both", "C) Regularisation increases both", "D) Simple models have low variance"], "A) More complex model → lower bias, higher variance", "hard", "model_evaluation", "Complex models fit training data well (low bias) but generalise poorly (high variance). Simpler models have the opposite."),
    ],
    "Deep Learning & Neural Networks": [
        ("What is a neuron in a neural network?", ["A) A weight matrix", "B) A unit that computes weighted sum + activation", "C) A layer of data", "D) A loss function"], "B) A unit that computes weighted sum + activation", "easy", "neural_networks", "A neuron computes: output = activation(weights · inputs + bias)."),
        ("Which activation function outputs values between 0 and 1?", ["A) ReLU", "B) Tanh", "C) Sigmoid", "D) Softmax"], "C) Sigmoid", "easy", "neural_networks", "Sigmoid: σ(x) = 1/(1+e^-x), output range (0, 1), used for binary classification."),
        ("What does backpropagation compute?", ["A) Forward pass predictions", "B) Gradients of loss with respect to weights", "C) Batch size", "D) Learning rate"], "B) Gradients of loss with respect to weights", "easy", "neural_networks", "Backpropagation uses chain rule to compute gradients, enabling gradient descent to update weights."),
        ("What is the purpose of MaxPooling in CNNs?", ["A) Add more features", "B) Reduce spatial dimensions and computation", "C) Normalise activations", "D) Prevent underfitting"], "B) Reduce spatial dimensions and computation", "medium", "deep_learning", "MaxPooling takes the maximum value in each window, reducing height/width while retaining dominant features."),
        ("What problem do LSTMs solve that vanilla RNNs cannot?", ["A) Overfitting", "B) Vanishing gradient — learning long-term dependencies", "C) Slow training", "D) Large memory usage"], "B) Vanishing gradient — learning long-term dependencies", "medium", "deep_learning", "LSTMs use gating mechanisms (forget, input, output gates) to maintain gradients over long sequences."),
        ("In transfer learning, why freeze base model weights?", ["A) Speed up inference", "B) Preserve learned features, only train new layers", "C) Reduce memory", "D) Prevent overfitting always"], "B) Preserve learned features, only train new layers", "medium", "deep_learning", "Freezing keeps ImageNet-learned features intact while the new head learns your specific task."),
        ("What is dropout regularisation?", ["A) Remove neurons permanently", "B) Randomly disable neurons during training to prevent co-adaptation", "C) Reduce learning rate", "D) Clip gradients"], "B) Randomly disable neurons during training to prevent co-adaptation", "hard", "neural_networks", "Dropout randomly zeros out neurons with probability p during training, forcing the network to learn redundant representations."),
        ("What does batch normalisation do?", ["A) Normalises input data", "B) Normalises layer activations to have mean≈0, std≈1 within a batch", "C) Increases batch size", "D) Reduces overfitting only"], "B) Normalises layer activations to have mean≈0, std≈1 within a batch", "hard", "deep_learning", "BatchNorm normalises activations within each mini-batch, stabilising training and allowing higher learning rates."),
    ],
    "Natural Language Processing": [
        ("What is tokenization in NLP?", ["A) Encrypting text", "B) Splitting text into individual units (words/subwords)", "C) Removing stopwords", "D) Translating text"], "B) Splitting text into individual units (words/subwords)", "easy", "nlp", "Tokenization converts raw text into a sequence of tokens that a model can process."),
        ("What are stopwords?", ["A) Words at end of sentence", "B) Common words like 'the', 'is', 'and' often removed in preprocessing", "C) Misspelled words", "D) Proper nouns"], "B) Common words like 'the', 'is', 'and' often removed in preprocessing", "easy", "nlp", "Stopwords are high-frequency words with little semantic content, often filtered out before analysis."),
        ("What is the key idea behind Word2Vec?", ["A) Count word frequencies", "B) Words appearing in similar contexts have similar meanings", "C) Translate words to numbers randomly", "D) Use grammar rules"], "B) Words appearing in similar contexts have similar meanings", "medium", "nlp", "Word2Vec trains on context windows — words co-occurring together get similar vector representations."),
        ("What does 'attention' do in transformers?", ["A) Reduces sequence length", "B) Allows each token to look at all other tokens and weigh their importance", "C) Speeds up computation", "D) Selects important sentences"], "B) Allows each token to look at all other tokens and weigh their importance", "medium", "nlp", "Self-attention computes how much each token should attend to every other token in the sequence."),
        ("What is the difference between BERT and GPT?", ["A) BERT generates text, GPT classifies", "B) BERT is bidirectional encoder, GPT is unidirectional decoder", "C) No difference", "D) BERT uses CNN, GPT uses RNN"], "B) BERT is bidirectional encoder, GPT is unidirectional decoder", "hard", "nlp", "BERT reads context from both directions (good for understanding). GPT reads left-to-right (good for generation)."),
    ],
    "Data Analysis & Statistics": [
        ("What does the mean represent?", ["A) Most frequent value", "B) Middle value", "C) Sum divided by count", "D) Maximum value"], "C) Sum divided by count", "easy", "statistics", "Mean = Σx / n — the arithmetic average of all values."),
        ("Which distribution is shaped like a bell curve?", ["A) Uniform", "B) Binomial", "C) Normal (Gaussian)", "D) Poisson"], "C) Normal (Gaussian)", "easy", "statistics", "The Normal distribution is symmetric around the mean with 68% of data within 1 standard deviation."),
        ("What does a p-value of 0.03 mean (with α=0.05)?", ["A) Accept null hypothesis", "B) Result is statistically significant — reject H₀", "C) No conclusion possible", "D) Need more data"], "B) Result is statistically significant — reject H₀", "medium", "statistics", "p=0.03 < α=0.05, so we reject the null hypothesis — the result is unlikely due to chance."),
        ("What is the IQR?", ["A) Mean minus median", "B) Q3 minus Q1 — middle 50% of data", "C) Max minus Min", "D) Standard deviation squared"], "B) Q3 minus Q1 — middle 50% of data", "easy", "statistics", "IQR = Q3 - Q1, representing the spread of the middle 50% of data, robust to outliers."),
        ("Pearson correlation of -0.9 means?", ["A) Weak positive relationship", "B) No relationship", "C) Strong negative relationship", "D) Moderate positive"], "C) Strong negative relationship", "medium", "statistics", "Correlation of -0.9 means as one variable increases, the other strongly decreases."),
        ("What is Type I error in hypothesis testing?", ["A) Accepting a false null hypothesis", "B) Rejecting a true null hypothesis (false positive)", "C) Using wrong test", "D) Small sample size"], "B) Rejecting a true null hypothesis (false positive)", "hard", "statistics", "Type I error (α) = false positive — concluding an effect exists when it doesn't."),
    ],
}


async def seed():
    """Main seed function."""
    async with AsyncSessionLocal() as db:
        # Check if already seeded
        existing = await db.execute(select(Course).limit(1))
        if existing.scalar_one_or_none():
            print("✓ Database already seeded. Skipping.")
            return

        print("Seeding database with DS/AI-ML content...")

        course_map = {}
        for course_data in COURSES:
            course = Course(**course_data)
            db.add(course)
            await db.flush()
            course_map[course_data["title"]] = course.id
            print(f"  ✓ Course: {course_data['title']}")

        # Seed lessons
        for course_title, lessons in LESSONS.items():
            course_id = course_map.get(course_title)
            if not course_id:
                continue
            for title, content, order, lesson_type in lessons:
                lesson = Lesson(
                    course_id=course_id,
                    title=title,
                    content=content,
                    order_index=order,
                    lesson_type=lesson_type,
                )
                db.add(lesson)
            print(f"  ✓ Lessons for: {course_title}")

        # Seed questions
        for course_title, questions in QUESTIONS.items():
            course_id = course_map.get(course_title)
            if not course_id:
                continue
            for q_text, options, correct, difficulty, topic, explanation in questions:
                question = Question(
                    course_id=course_id,
                    question_text=q_text,
                    options=options,
                    correct_answer=correct,
                    difficulty=difficulty,
                    topic_tag=topic,
                    explanation=explanation,
                )
                db.add(question)
            print(f"  ✓ Questions for: {course_title}")

        await db.commit()
        print("\n✅ Database seeded successfully!")
        print(f"   {len(COURSES)} courses")
        total_lessons = sum(len(v) for v in LESSONS.values())
        total_questions = sum(len(v) for v in QUESTIONS.values())
        print(f"   {total_lessons} lessons")
        print(f"   {total_questions} questions (easy/medium/hard)")
        print("\nYou can now:")
        print("   1. Register an account at http://localhost:5173")
        print("   2. Test the API at http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(create_tables())
    asyncio.run(seed())