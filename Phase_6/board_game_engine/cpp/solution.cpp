#include<bits/stdc++.h>
using namespace std;

struct Player { string id, name; int pos = 0; };

class Command {
public:
    virtual bool execute() = 0;
    virtual void undo() = 0;
    virtual ~Command() = default;
};

class Board {
    int sz;
    unordered_map<int,int> snakes, ladders;
public:
    Board(int s, unordered_map<int,int> sn = {}, unordered_map<int,int> ld = {})
        : sz(s), snakes(move(sn)), ladders(move(ld)) {}
    int size() const { return sz; }
    int process(int pos) const {
        auto it = snakes.find(pos);
        if (it != snakes.end()) return it->second;
        it = ladders.find(pos);
        if (it != ladders.end()) return it->second;
        return pos;
    }
};

class MoveCommand : public Command {
    Player& player;
    const Board& board;
    int dice, old_pos;
public:
    MoveCommand(Player& p, const Board& b, int d) : player(p), board(b), dice(d), old_pos(p.pos) {}
    bool execute() override {
        int np = player.pos + dice;
        if (np > board.size()) return false;
        player.pos = board.process(np);
        return true;
    }
    void undo() override { player.pos = old_pos; }
};

class GameEngine {
    Board board;
    vector<Player> players;
    int turn = 0;
    vector<unique_ptr<Command>> history;
    Player* winner = nullptr;
    mutex mtx;
    mt19937 rng{42};
public:
    GameEngine(Board b) : board(move(b)) {}
    Player& add_player(const string& id, const string& name) {
        lock_guard<mutex> lk(mtx);
        players.push_back({id, name, 0});
        return players.back();
    }
    struct TurnResult { string player; int dice, from_pos, to_pos; bool moved, won; };
    TurnResult play_turn(int dice_override = -1) {
        lock_guard<mutex> lk(mtx);
        if (winner) throw runtime_error("Game over");
        auto& p = players[turn % players.size()];
        int dice = dice_override >= 0 ? dice_override : uniform_int_distribution<>(1, 6)(rng);
        int old = p.pos;
        auto cmd = make_unique<MoveCommand>(p, board, dice);
        bool moved = cmd->execute();
        bool won = false;
        if (moved) {
            if (p.pos == board.size()) { winner = &p; won = true; }
            history.push_back(move(cmd));
        }
        turn++;
        return {p.name, dice, old, p.pos, moved, won};
    }
    bool undo_move() {
        lock_guard<mutex> lk(mtx);
        if (history.empty()) return false;
        history.back()->undo(); history.pop_back(); turn--; winner = nullptr;
        return true;
    }
    Player* get_winner() { lock_guard<mutex> lk(mtx); return winner; }
    vector<pair<string,int>> standings() {
        lock_guard<mutex> lk(mtx);
        vector<pair<string,int>> s;
        for (auto& p : players) s.push_back({p.name, p.pos});
        sort(s.begin(), s.end(), [](auto& a, auto& b) { return a.second > b.second; });
        return s;
    }
};

int main() {
    Board board(20, {{15, 5}}, {{3, 12}});
    GameEngine engine(board);
    engine.add_player("p1", "Alice");
    engine.add_player("p2", "Bob");

    // Ladder test
    auto r = engine.play_turn(3); // Alice: 0+3=3 -> ladder -> 12
    assert(r.to_pos == 12 && r.moved);

    // Undo
    assert(engine.undo_move());
    assert(engine.standings()[0].second == 0);

    // Snake test
    engine.play_turn(4); // Alice -> 4
    engine.play_turn(1); // Bob -> 1
    engine.play_turn(11); // Alice: 4+11=15 -> snake -> 5
    assert(engine.standings().size() == 2);

    // Win test
    auto& alice = engine.standings()[0]; // find Alice
    // Reset for clean win test
    GameEngine e2(Board(10, {}, {}));
    e2.add_player("p1", "A");
    auto r2 = e2.play_turn(10); // A -> 10 = board size
    assert(r2.won);
    assert(e2.get_winner() != nullptr);

    // Game over blocks play
    try { e2.play_turn(1); assert(false); } catch (runtime_error&) {}

    // Can't exceed board
    GameEngine e3(Board(10, {}, {}));
    e3.add_player("p1", "A");
    e3.play_turn(8); // A -> 8
    auto r3 = e3.play_turn(5); // 8+5=13 > 10
    assert(!r3.moved);

    cout << "Complete C++ Board Game tests passed!" << endl;
}
