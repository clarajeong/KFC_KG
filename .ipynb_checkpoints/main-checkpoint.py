from make_question import make_question
from entity import extractNconvert_entity
from entity import convert_final
import test_manually
import blanked_test_manually
import argparse


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some integers.")
    parser.add_argument('startword', type=str, help='Startword')
    parser.add_argument('hop_type', type=int, help='hop_type')
    parser.add_argument('q_id', type=str, help='q_id')
    parser.add_argument('--normal_test', type=bool, default=False, help='NORMAL VERSION TEST')
    parser.add_argument('--blanked', type=bool, default=False, help='BLANKED VERSION TEST')

    args = parser.parse_args()
    
    
    print(f"Got argument: {args.startword}, {args.hop_type}, {args.q_id}, normal_test: {args.normal_test}, blanked: {args.blanked}")
    result = make_question(args.startword, args.hop_type, args.q_id)
    extractNconvert_entity(args.q_id)
    convert_final(args.q_id)
    blanked_test_manually.update_QA()
    if args.normal_test:
        test_manually.ask_gpt_manually([args.q_id])
    if args.blanked:
        blanked_test_manually.ask_gpt_manually([0, 1, 2, 4])