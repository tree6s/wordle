import requests
import random
import string
import time

# 随机生成一个单词
def generate_random_word(length=5, IsStart=False):
    base_word_dict = {
        2: 'ae',  # 最常见的字母
        3: 'ear',
        4: 'eart',
        5: 'earot',
        6: 'eariot',
        7: 'eariotn',
        8: 'eariotns',
        9: 'eariotns'
    }
    if IsStart:
        return base_word_dict[length]
    else:
        return ''.join(random.choices(string.ascii_lowercase, k=length))

# 调用API猜测随机单词（增加延时和重试机制）
def get_api_feedback_random(guess, size=5, seed=None, max_retries=3, delay=1):
    url = "https://wordle.votee.dev:8000/random"  # 替换为实际 API 地址
    params = {"guess": guess, "size": size}
    if seed is not None:
        params["seed"] = seed  # 添加 seed 参数
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=5)  # 设置超时时间
            if response.status_code == 200:
                return response.json()  # 返回JSON格式
            else:
                print(f"API 请求失败: {response.status_code} - {response.text}")
        except requests.RequestException as e:
            print(f"API 请求异常: {e}")
        # 延时后重试
        time.sleep(delay)
    print("API 请求多次失败，终止程序。")
    return None

# 根据反馈动态生成下一个单词
def generate_next_guess(current_guess, feedback, correct_letters, present_letters, absent_letters, guessed_words, word_length=5):
    new_guess = list(current_guess)  # 当前猜测的基础
    for i, fb in enumerate(feedback):
        if fb == 'correct':  # Correct: 固定该位置的字母
            correct_letters[i] = current_guess[i]
        elif fb == 'present':  # Present: 字母存在，但位置错误
            present_letters.add((current_guess[i], i))  # 保存字母和错误的位置
            new_guess[i] = None  # 清空当前字母，准备替换
        elif fb == 'absent':  # Absent: 字母不存在
            absent_letters.add(current_guess[i])

    # 根据约束生成新单词
    for i in range(word_length):
        if i in correct_letters:
            new_guess[i] = correct_letters[i]  # 保留正确位置的字母
        elif new_guess[i] is None or new_guess[i] in absent_letters:
            while True:
                random_letter = random.choice(string.ascii_lowercase)
                if random_letter not in absent_letters:
                    new_guess[i] = random_letter
                    break

    # 确保 new_guess 包含所有 present_letters，但避开错误位置
    for letter, wrong_position in present_letters:
        if letter not in new_guess:
            for i in range(word_length):
                if i not in correct_letters and i != wrong_position and new_guess[i] not in present_letters:
                    new_guess[i] = letter
                    break

    # 将新单词转换为字符串形式
    next_guess = ''.join(new_guess)

    # 避免重复猜测
    while next_guess in guessed_words:
        next_guess = generate_random_word(word_length)  # 随机生成一个新单词

    # 添加到已猜测集合
    guessed_words.add(next_guess)

    return next_guess



# 随机猜单词的求解器（增加最大尝试次数限制和延时）
def solve_random_word(seed=None, max_attempts=100, delay=1):
    size = 5  # 单词长度
    attempts = 0
    success = False
    guessed_words = set()  # 记录已猜测的单词

    # 初始化约束条件
    correct_letters = {}  # 位置已确定的字母，例如 {0: 'a', 2: 'c'}
    present_letters = set()  # 存在但位置不正确的字母，例如 {'b', 'd'}
    absent_letters = set()  # 不存在的字母，例如 {'x', 'z'}

    print(f"开始随机猜单词任务 (seed={seed})!")
    
    current_guess = generate_random_word(size, IsStart=True)  # 初始猜测
    guessed_words.add(current_guess)  # 添加初始猜测到集合
    while not success and attempts < max_attempts:
        attempts += 1
        print(f"第 {attempts} 次猜测: {current_guess}")

        # 调用API进行猜测
        feedback = get_api_feedback_random(current_guess, size, seed=seed, delay=delay)
        if feedback is None:
            print("无法获取反馈，结束程序。")
            return

        # 解析反馈
        feedback_results = [item["result"] for item in feedback]
        print(f"反馈: {feedback_results}")

        # 检查是否猜对
        if all(res == 'correct' for res in feedback_results):  # 全部为 'correct' 表示猜对
            print(f"恭喜！在第 {attempts} 次猜测中成功猜出答案: {current_guess}")
            success = True
            break

        # 根据反馈更新下一次猜测
        current_guess = generate_next_guess(
            current_guess,
            feedback_results,
            correct_letters,
            present_letters,
            absent_letters,
            guessed_words,  # 传入已猜测集合
            word_length=size
        )
        # 增加延时，避免过于频繁调用API
        time.sleep(delay)

    if not success:
        print("超过最大尝试次数，未能成功猜出答案。")

# 运行程序
if __name__ == "__main__":
    # 传递 seed 参数以控制随机性，增加 API 调用间隔
    solve_random_word(seed=12345, delay=2)
