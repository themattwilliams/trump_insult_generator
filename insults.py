# Import required modules
import random
import json
import sys
import pyperclip

# Load quotes from JSON file
with open('trump.json', 'r') as f:
    quotes = json.load(f)

# Define insult templates
templates = [
    ["subjectnametwice1", "user_name", "subjectnametwice2", "user_name", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["user_name", "subjectnamefirst", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
    ["subjectnamesecond", "user_name", "predicate", "insult3", "kicker"],
]

# Define nice quotes to use instead of insults for specific names
niceQuotes = [
  "What a beautiful person!",
  "That one should be our president!",
  "I know the best people. And that's one of them.",
  "Fantastic, yuge potential!",
]

# Define function to generate insults
def generate_insult(name):
    # Convert name to lowercase for case-insensitive comparison
    name = name.lower()
    # Check if name matches specific names for nice quotes
    if 'donald' in name or 'trump' in name or 'ivanka' in name:
        # Return a random nice quote
        return random.choice(niceQuotes)

    # Choose a random template
    template = random.choice(templates)

    # Build the insult phrase
    words = []
    for i, word in enumerate(template):
        if word == "user_name":
            # Add the name to the phrase with title case
            words.append(name.title())
        else:
            # Choose a random word from the quotes for the given word
            words.append(random.choice(quotes[word]))

        # Remove extra space before the name if it's the first word
        if i == 0 and words[0][-1] == ',':
            words[0] = words[0][:-1]

        # Remove extra space after the name if it's the last word
        if i == len(template) - 1 and words[-1][-1] == ',':
            words[-1] = words[-1][:-1]

    # Join the words into a single string with spaces and strip extra spaces
    return ' '.join(words).strip()

# Main function to get name from command line and generate insult
def main():
    # Check if name was provided as a command-line argument
    if len(sys.argv) < 2:
        print("Usage: python insults.py [name]")
        return

    # Get the name from the command line argument and strip any extra spaces
    name = sys.argv[1].strip()

    # Generate the insult
    insult = generate_insult(name)

    # Copy the insult to the clipboard
    pyperclip.copy(insult)

    # Print the insult
    print(insult)

if __name__ == '__main__':
    main()