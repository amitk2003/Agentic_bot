import asyncio
import json
from app.agent.schemas import UserInput
from app.agent.orchestrator import process_request

code = """Explain this code:

#include <bits/stdc++.h>
using namespace std;

string longestPalindromeSubseq(string s) {
    int n = s.size();

    vector<vector<int>> dp(n, vector<int>(n, 0));

    // Base case
    for (int i = 0; i < n; i++)
        dp[i][i] = 1;

    // Fill DP table
    for (int len = 2; len <= n; len++) {
        for (int i = 0; i + len - 1 < n; i++) {
            int j = i + len - 1;

            if (s[i] == s[j]) {
                if (len == 2)
                    dp[i][j] = 2;
                else
                    dp[i][j] = 2 + dp[i + 1][j - 1];
            } else {
                dp[i][j] = max(dp[i + 1][j], dp[i][j - 1]);
            }
        }
    }

    int length = dp[0][n - 1];
    string ans(length, ' ');

    int start = 0;
    int end = length - 1;

    int i = 0, j = n - 1;

    while (i <= j) {
        if (s[i] == s[j]) {
            ans[start] = s[i];
            ans[end] = s[j];
            start++;
            end--;
            i++;
            j--;
        } else if (dp[i + 1][j] >= dp[i][j - 1]) {
            i++;
        } else {
            j--;
        }
    }

    return ans;
}

int main() {
    string s = "bbbab";

    cout << "Longest Palindromic Subsequence: "
         << longestPalindromeSubseq(s) << endl;
}"""

async def main():
    try:
        res = await process_request(UserInput(query=code, files=[], chat_history=[]))
        with open('test_output2.json', 'w', encoding='utf-8') as f:
            f.write(res.model_dump_json())
    except Exception as e:
        with open('test_output2.json', 'w', encoding='utf-8') as f:
            f.write(json.dumps({"error": str(e)}))

asyncio.run(main())
