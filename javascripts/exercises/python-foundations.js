(() => {
  "use strict";

  /*
   * Learning Hub
   * Python Foundations Exercise Pack
   *
   * V4.7C
   *
   * Mapping:
   *
   * Bài 002 — Biến, giá trị và kiểu dữ liệu
   *   001, 002, 006, 011
   *
   * Bài 004 — Phép toán, chuyển kiểu và máy tính mini
   *   003, 004, 005, 007,
   *   008, 009, 010, 012
   */

  const catalog =
    window.LearningHubExerciseCatalog;

  if (!catalog) {
    console.error(
      "[Learning Hub] Exercise Catalog chưa được tải."
    );
    return;
  }

  catalog.registerMany([

    // ========================================================
    // BÀI 002
    // Biến, giá trị và các kiểu dữ liệu cơ bản
    // ========================================================

    {
      id: "python-foundation-001",
      language: "python",
      chapter: "foundations",
      lessonId: "python-variables",
      lessonNumber: "002",
      difficulty: 1,

      title: "Tạo tên cho người chơi",

      description:
        "Tạo biến player_name có giá trị Learning Hero rồi in tên người chơi ra màn hình.",

      starterCode:
`# Tạo biến player_name ở đây


print(player_name)`,

      tests: [
        {
          type: "output",
          expected: "Learning Hero",
          label:
            "Tên người chơi phải là Learning Hero"
        }
      ],

      hints: [
        "Một biến có thể lưu dữ liệu để dùng lại sau.",
        "Chuỗi chữ (string) cần đặt trong dấu nháy.",
        `player_name = "Learning Hero"`
      ]
    },

    {
      id: "python-foundation-002",
      language: "python",
      chapter: "foundations",
      lessonId: "python-variables",
      lessonNumber: "002",
      difficulty: 1,

      title: "Tạo số coins",

      description:
        "Player bắt đầu game với 20 coins. Tạo biến coins rồi in giá trị của nó.",

      starterCode:
`# Player bắt đầu với 20 coins
coins = 0

print(coins)`,

      tests: [
        {
          type: "output",
          expected: "20",
          label:
            "Player phải có 20 coins"
        }
      ],

      hints: [
        "coins là một biến chứa số.",
        "Bạn chỉ cần thay giá trị đang gán cho coins.",
        "coins = 20"
      ]
    },

    {
      id: "python-foundation-006",
      language: "python",
      chapter: "foundations",
      lessonId: "python-strings",
      lessonNumber: "002",
      difficulty: 1,

      title: "Tạo tên nhân vật",

      description:
        "Ghép class_name và hero_name để chương trình in đúng: Mage Luna",

      starterCode:
`class_name = "Mage"
hero_name = "Luna"

character = ""

# Ghép tên ở đây


print(character)`,

      tests: [
        {
          type: "output",
          expected: "Mage Luna",
          label:
            "Tên đầy đủ phải là Mage Luna"
        }
      ],

      hints: [
        "Hai string có thể nối bằng dấu +.",
        "Đừng quên khoảng trắng giữa Mage và Luna.",
        `character = class_name + " " + hero_name`
      ]
    },

    {
      id: "python-foundation-011",
      language: "python",
      chapter: "foundations",
      lessonId: "python-debug-basics",
      lessonNumber: "002",
      difficulty: 2,

      title: "Sửa tên item",

      description:
        "Code hiện in SwordLegendary nhưng UI game cần hiển thị Sword Legendary. Hãy sửa code.",

      starterCode:
`item = "Sword"
rarity = "Legendary"

item_name = item + rarity

print(item_name)`,

      tests: [
        {
          type: "output",
          expected: "Sword Legendary",
          label:
            "Tên item phải có khoảng trắng"
        }
      ],

      hints: [
        "Hai từ cần được ngăn cách.",
        "Có thể chèn một string chứa đúng một khoảng trắng.",
        `item_name = item + " " + rarity`
      ]
    },


    // ========================================================
    // BÀI 004
    // Phép toán, chuyển kiểu và máy tính mini
    // ========================================================

    {
      id: "python-foundation-003",
      language: "python",
      chapter: "foundations",
      lessonId: "python-basic-math",
      lessonNumber: "004",
      difficulty: 1,

      title: "Nhặt thêm coins",

      description:
        "Player có 7 coins và nhặt thêm 5. Hãy tính tổng số coins.",

      starterCode:
`coins = 7
collected = 5

total = 0

# Tính total ở đây


print(total)`,

      tests: [
        {
          type: "output",
          expected: "12",
          label:
            "Tổng coins phải bằng 12"
        }
      ],

      hints: [
        "Bạn cần cộng coins và collected.",
        "Python dùng dấu + để cộng.",
        "total = coins + collected"
      ]
    },

    {
      id: "python-foundation-004",
      language: "python",
      chapter: "foundations",
      lessonId: "python-basic-math",
      lessonNumber: "004",
      difficulty: 1,

      title: "Player nhận sát thương",

      description:
        "Player đang có 100 HP và nhận 25 damage. Hãy tính lượng HP còn lại.",

      starterCode:
`health = 100
damage = 25

# Cập nhật health ở đây


print(health)`,

      tests: [
        {
          type: "output",
          expected: "75",
          label:
            "Player phải còn 75 HP"
        }
      ],

      hints: [
        "Damage làm health giảm xuống.",
        "Phép trừ trong Python dùng dấu -.",
        "health = health - damage"
      ]
    },

    {
      id: "python-foundation-005",
      language: "python",
      chapter: "foundations",
      lessonId: "python-basic-math",
      lessonNumber: "004",
      difficulty: 1,

      title: "Tính damage của đòn combo",

      description:
        "Một hit gây 8 damage. Combo đánh trúng 4 hit. Hãy tính tổng damage.",

      starterCode:
`damage_per_hit = 8
hits = 4

total_damage = 0

# Tính damage của combo


print(total_damage)`,

      tests: [
        {
          type: "output",
          expected: "32",
          label:
            "Combo phải gây 32 damage"
        }
      ],

      hints: [
        "Mỗi hit gây cùng một lượng damage.",
        "Có thể dùng phép nhân thay vì cộng 8 bốn lần.",
        "total_damage = damage_per_hit * hits"
      ]
    },

    {
      id: "python-foundation-007",
      language: "python",
      chapter: "foundations",
      lessonId: "python-basic-math",
      lessonNumber: "004",
      difficulty: 2,

      title: "Tính điểm sau trận đấu",

      description:
        "Player có 1200 điểm, nhận thêm 350 điểm và bị trừ 100 điểm phạt. Hãy tính điểm cuối.",

      starterCode:
`score = 1200
reward = 350
penalty = 100

final_score = 0

# Tính điểm cuối


print(final_score)`,

      tests: [
        {
          type: "output",
          expected: "1450",
          label:
            "Điểm cuối phải bằng 1450"
        }
      ],

      hints: [
        "Đầu tiên cộng reward vào score.",
        "Sau đó trừ penalty.",
        "final_score = score + reward - penalty"
      ]
    },

    {
      id: "python-foundation-008",
      language: "python",
      chapter: "foundations",
      lessonId: "python-basic-math",
      lessonNumber: "004",
      difficulty: 2,

      title: "Robot di chuyển tới vị trí mới",

      description:
        "Robot đang ở x = 10 và tiến thêm 7 đơn vị. Hãy tính vị trí x mới.",

      starterCode:
`x = 10
movement = 7

new_x = 0

# Tính vị trí mới


print(new_x)`,

      tests: [
        {
          type: "output",
          expected: "17",
          label:
            "Robot phải tới x = 17"
        }
      ],

      hints: [
        "Vị trí mới phụ thuộc vào vị trí cũ và quãng đường di chuyển.",
        "Robot đang tiến về phía dương.",
        "new_x = x + movement"
      ]
    },

    {
      id: "python-foundation-009",
      language: "python",
      chapter: "foundations",
      lessonId: "python-basic-math",
      lessonNumber: "004",
      difficulty: 2,

      title: "Tính số potion còn lại",

      description:
        "Inventory có 12 potion. Player dùng 3 và sau đó nhặt thêm 5. Hãy tính số potion cuối cùng.",

      starterCode:
`potions = 12
used = 3
found = 5

remaining = 0

# Tính số potion cuối cùng


print(remaining)`,

      tests: [
        {
          type: "output",
          expected: "14",
          label:
            "Inventory phải có 14 potion"
        }
      ],

      hints: [
        "Potion đã dùng phải bị trừ.",
        "Potion vừa tìm thấy phải được cộng.",
        "remaining = potions - used + found"
      ]
    },

    {
      id: "python-foundation-010",
      language: "python",
      chapter: "foundations",
      lessonId: "python-debug-basics",
      lessonNumber: "004",
      difficulty: 2,

      title: "Debug hệ thống XP",

      description:
        "Đoạn code đang tính XP sai. Player phải có tổng cộng 150 XP. Hãy sửa lỗi.",

      starterCode:
`xp = 100
earned_xp = 50

# BUG: phép tính bên dưới đang sai
xp = xp - earned_xp

print(xp)`,

      tests: [
        {
          type: "output",
          expected: "150",
          label:
            "XP sau khi nhận thưởng phải bằng 150"
        }
      ],

      hints: [
        "earned_xp là XP được nhận thêm.",
        "Nhận thêm XP thì tổng XP phải tăng.",
        "Đổi dấu - thành dấu +."
      ]
    },

    {
      id: "python-foundation-012",
      language: "python",
      chapter: "foundations",
      lessonId: "python-foundation-challenge",
      lessonNumber: "004",
      difficulty: 3,

      title:
        "Mini Challenge — Tính vàng sau nhiệm vụ",

      description:
        "Hero có 250 gold. Nhiệm vụ thưởng 120 gold. Hero mua potion giá 35 gold và mua 2 potion. Hãy tính số gold cuối cùng.",

      starterCode:
`gold = 250
quest_reward = 120

potion_price = 35
potion_count = 2

# Tính tổng tiền mua potion
shopping_cost = 0

# Tính gold cuối cùng
final_gold = 0


print(final_gold)`,

      tests: [
        {
          type: "output",
          expected: "300",
          label:
            "Hero phải còn 300 gold"
        }
      ],

      hints: [
        "Trước tiên tính giá của 2 potion.",
        "shopping_cost = potion_price * potion_count",
        "final_gold = gold + quest_reward - shopping_cost"
      ]
    }

  ]);

})();