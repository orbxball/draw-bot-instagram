import argparse
import math
import json
from selenium import webdriver
from time import sleep
# Find the correct version of chromedriver automatically
# https://stackoverflow.com/questions/60296873/sessionnotcreatedexception-message-session-not-created-this-version-of-chrome
from webdriver_manager.chrome import ChromeDriverManager


def main(args):
    config_path = './config.json' if not args.config else args.config
    with open(config_path, 'r+') as f:
        config = json.load(f)

    # path for the chromedriver
    oper_sys = config['oper_sys']
    driver_name = '/chromedriver.exe' if oper_sys == 'windows' else '/chromedriver'
    driver_path = oper_sys.lower() + driver_name
    driver = webdriver.Chrome(ChromeDriverManager().install())

    # user data and draw's profile
    username = config['username']
    password = config['password']
    post_link = config['post_link']

    access_account(driver, username, password)

    # load from last time `usernames_list` directly
    if args.load:
        with open('usernames_list.json', 'r+') as f:
            data = json.load(f)
            print("loaded 'usernames_list.json'...")
            usernames_list = data['usernames_list']
    # login instagram account page to get `usernames_list`
    else:
        usernames_list = get_usernames_list(args, config, driver)
        data = {"usernames_list": usernames_list}
        with open('usernames_list.json', 'w+') as f:
            json.dump(data, f)
            print("saved 'usernames_list.json'...")

    # see if we need to continue from last time breakpoint IG handle
    if args.breakpoint:
        try:
            idx = usernames_list.index(args.breakpoint)
        except ValueError:
            print("Instagram name @{} does not exist! Please check it again!!!".format(args.breakpoint))
            return
        usernames_list = usernames_list[idx+1:]

    print("Number of tagged: {}".format(len(usernames_list)))
    search_profile(driver, usernames_list, post_link, args.num, args.comment)


# login on instagram
def access_account(driver, username, password):
    driver.get("https://www.instagram.com")
    sleep(3)

    print('Logging on Instagram...')
    driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div[1]/div/form/div[2]/div/label/input').send_keys(username)
    driver.find_element_by_xpath('//*[@id="react-root"]/section/main/article/div[2]/div[1]/div/form/div[3]/div/label/input').send_keys(password)
    driver.find_element_by_xpath('//button[@type="submit"]').click()
    sleep(4)

    # Sometimes Instagram will ask you if you want to save the login info
    # Thus, we need to check if you enter into that page
    # Need to skip that page with "Not Now" and keep going
    try:
        # Go to account page
        driver.find_element_by_xpath('/html/body/div[4]/div/div/div[3]/button[2]').click()
        sleep(2)
    except:
        # Click on "Not Now"
        driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/div/div/div/button').click()
        sleep(2)

        # Go to account page
        driver.find_element_by_xpath('/html/body/div[4]/div/div/div[3]/button[2]').click()
        sleep(2)


# get `usernames_list` from whitelist or account page
def get_usernames_list(args, config, driver):
    usernames_list = []
    # if whitelist is on, use this
    if args.whitelist:
        print("Using whitelist...")
        usernames_list = config['usernames_list']
    else:
        usernames_set = set()
        if args.followers:
            followers_set = set(get_followers(driver))
            rm_set = set()
            if args.only:
                rm_set.update(get_following(driver))
            usernames_set.update(followers_set - rm_set)
        if args.following:
            following_set = set(get_following(driver))
            rm_set = set()
            if args.only:
                rm_set.update(get_followers(driver))
            usernames_set.update(following_set - rm_set)
        usernames_list = list(usernames_set)
        usernames_list.sort() # guaranteed the order

    # remove blacklist
    blacklist = config['blacklist']
    for handle in blacklist:
        if handle in usernames_list:
            usernames_list.remove(handle)

    return usernames_list


# capture the followers's usernames
def get_followers(driver):
    print("Accessing follower's list...")

    driver.find_element_by_xpath('//*[@id="react-root"]/section/nav/div[2]/div/div/div[3]/div/div[5]/a').click()
    sleep(3)
    driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a').click()
    sleep(3)

    # get number of followers
    followers_number = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[2]/a/span').get_attribute('textContent')

    if '.' in followers_number:
        followers_number = followers_number.replace('.', '')

    list_to_scroll = driver.find_element_by_xpath('/html/body/div[4]/div/div[2]/ul/div')
    sleep(2)

    # scroll the followers's list to the end
    print("Getting follower's names...")
    scroll_times = int(math.ceil(int(followers_number) / 8))
    for i in range(scroll_times):
        driver.execute_script('document.querySelector(".PZuss").scrollIntoView(false)')
        sleep(2)

    # get each username in the followers's list
    print("Putting names in a list...")
    usernames_elements = list_to_scroll.find_elements_by_tag_name('a')
    usernames_list = [user.text for user in usernames_elements if len(user.text) > 0]
    sleep(2)

    driver.refresh()
    sleep(2)

    return usernames_list


# capture the following's usernames
def get_following(driver):
    print("Accessing following's list...")

    driver.find_element_by_xpath('//*[@id="react-root"]/section/nav/div[2]/div/div/div[3]/div/div[5]/a').click()
    sleep(3)
    driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a').click()
    sleep(3)

    # get number of following
    following_number = driver.find_element_by_xpath('//*[@id="react-root"]/section/main/div/header/section/ul/li[3]/a/span').get_attribute('textContent')

    if '.' in following_number:
        following_number = following_number.replace('.', '')

    list_to_scroll = driver.find_element_by_xpath('/html/body/div[4]/div/div[2]/ul/div')
    sleep(2)

    # scroll the following's list to the end
    print("Getting following's names...")
    scroll_times = int(math.ceil(int(following_number) / 8))
    for i in range(scroll_times):
        driver.execute_script('document.querySelector(".PZuss").scrollIntoView(false)')
        sleep(2)

    # get each username in the following's list
    print("Putting names in a list...")
    usernames_elements = list_to_scroll.find_elements_by_tag_name('a')
    usernames_list = [user.text for user in usernames_elements if len(user.text) > 0]
    sleep(2)

    driver.refresh()
    sleep(2)

    return usernames_list


# search the draw's profile and publication
def search_profile(driver, usernames, post_link, n, comment):
    driver.get(post_link)

    print("Commenting on post...")
    for i in range(0, len(usernames), n):
        can_press = True

        while can_press:
            try:
                # click on comment area
                driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div[1]/article/div[2]/section[3]/div/form/textarea').click()
                sleep(4)
                can_press = False
            except:
                try:
                    # press post button if comment is blocked
                    driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div[1]/article/div[2]/section[3]/div/form/button').click()
                    sleep(4)
                except:
                    sleep(180)

        print('the above comment Succeed!')

        # write follower's username
        message = ''
        for j in range(0, n):
            message += '@' + usernames[i+j] + ' '
        message += comment
        driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div[1]/article/div[2]/section[3]/div/form/textarea').send_keys(message)
        sleep(2)

        # press post button
        driver.find_element_by_xpath('/html/body/div[1]/section/main/div/div[1]/article/div[2]/section[3]/div/form/button').click()
        sleep(2)

        print(message)
        sleep(60)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A Tool to automatically tag people and post on Instagram to join in a draw!\nIn default, it reads `config.json` to get configuration.\n",formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--num", type=int, required=True, help="number of people being tagged")
    parser.add_argument("--comment", type=str, required=True, help="comment after tagging people")
    parser.add_argument("--config", type=str, help="path of configuration file, default: './config.json'")
    parser.add_argument("--whitelist", action="store_true", help="if you want to use the `usernames_list` in config, turn on this option")
    parser.add_argument("--followers", action="store_true", help="if you want to tag all followers, turn on this option")
    parser.add_argument("--following", action="store_true", help="if you want to tag all followings, turn on this option")
    parser.add_argument("--only", action="store_true", help="if this option is turned on, the intersection of 'folllowers' and 'following' would be removed. It would be 'only followers' or 'only following'")
    parser.add_argument("--breakpoint", type=str, help="put the last successful ig id here to keep continuing", metavar="IG_NAME")
    parser.add_argument("--load", action="store_true", help="if you want to load 'usernames_list' saved from last time, turn on this option")
    args = parser.parse_args()

    main(args)
